from __future__ import annotations

import logging
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db
from app.dependencies import get_current_user
from app.models.trade import Trade
from app.models.user import User
from app.schemas.trade import TradeOut, TradeListResponse, UploadResponse
from app.engine.csv_parser import parse_csv, validate_csv_size

logger = logging.getLogger("tradeloop.trades")
settings = get_settings()
router = APIRouter(prefix="/trades", tags=["trades"])

UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
VALID_BROKERS = {"auto", "generic", "zerodha", "mt4"}


@router.post("/upload", response_model=UploadResponse)
async def upload_csv(
    file: UploadFile = File(...),
    broker: str = Query("auto", description="Broker format: auto, generic, zerodha, mt4"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if broker not in VALID_BROKERS:
        raise HTTPException(status_code=400, detail=f"Invalid broker. Must be one of: {', '.join(VALID_BROKERS)}")

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")

    raw = await file.read()
    if len(raw) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 5MB.")

    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding not supported. Please use UTF-8.")

    size_error = validate_csv_size(content)
    if size_error:
        raise HTTPException(status_code=413, detail=size_error)

    # Free tier enforcement
    if user.plan == "free":
        existing_count_result = await db.execute(
            select(func.count()).select_from(Trade).where(Trade.user_id == user.id)
        )
        existing_count = existing_count_result.scalar() or 0
        remaining = max(0, settings.free_tier_trade_limit - existing_count)
        if remaining == 0:
            raise HTTPException(
                status_code=403,
                detail=f"Free tier limit reached ({settings.free_tier_trade_limit} trades). Upgrade to Pro for unlimited trades."
            )

    parsed, parse_errors = parse_csv(content, broker=broker)

    if not parsed:
        detail = "No valid trades found in the CSV."
        if parse_errors:
            detail += " Errors: " + "; ".join(parse_errors[:3])
        raise HTTPException(status_code=400, detail=detail)

    # Apply free tier cap
    if user.plan == "free":
        parsed = parsed[:remaining]

    imported = 0
    skipped = 0
    errors = list(parse_errors[:5])

    for trade_data in parsed:
        try:
            trade = Trade(
                user_id=user.id,
                timestamp=trade_data.timestamp,
                symbol=trade_data.symbol,
                side=trade_data.side,
                entry_price=trade_data.entry_price,
                exit_price=trade_data.exit_price,
                quantity=trade_data.quantity,
                pnl=trade_data.pnl,
                duration_minutes=trade_data.duration_minutes,
                setup_type=trade_data.setup_type,
                notes=trade_data.notes,
                fees=trade_data.fees,
            )
            db.add(trade)
            imported += 1
        except Exception as e:
            skipped += 1
            errors.append(str(e))

    await db.flush()
    logger.info("User %s uploaded %d trades (skipped: %d)", user.email, imported, skipped)
    return UploadResponse(imported=imported, skipped=skipped, errors=errors[:5])


@router.get("", response_model=TradeListResponse)
async def list_trades(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    symbol: Optional[str] = Query(None),
    side: Optional[str] = Query(None),
    sort_by: str = Query("timestamp", description="Sort field: timestamp, pnl, symbol"),
    sort_dir: str = Query("desc", description="Sort direction: asc, desc"),
    search: Optional[str] = Query(None, description="Search by symbol name"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(Trade).where(Trade.user_id == user.id)
    count_query = select(func.count()).select_from(Trade).where(Trade.user_id == user.id)

    if symbol:
        query = query.where(Trade.symbol == symbol.upper())
        count_query = count_query.where(Trade.symbol == symbol.upper())

    if side and side.upper() in ("BUY", "SELL"):
        query = query.where(Trade.side == side.upper())
        count_query = count_query.where(Trade.side == side.upper())

    if search:
        query = query.where(Trade.symbol.contains(search.upper()))
        count_query = count_query.where(Trade.symbol.contains(search.upper()))

    sort_col_map = {"timestamp": Trade.timestamp, "pnl": Trade.pnl, "symbol": Trade.symbol}
    sort_col = sort_col_map.get(sort_by, Trade.timestamp)
    order = sort_col.desc() if sort_dir == "desc" else sort_col.asc()

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(order).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    trades = result.scalars().all()

    return TradeListResponse(
        trades=[TradeOut(id=str(t.id), **{
            k: getattr(t, k) for k in TradeOut.model_fields if k != "id"
        }) for t in trades],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/symbols")
async def list_symbols(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Trade.symbol, func.count()).where(Trade.user_id == user.id)
        .group_by(Trade.symbol).order_by(func.count().desc())
    )
    return [{"symbol": row[0], "count": row[1]} for row in result.all()]


@router.delete("/{trade_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trade(
    trade_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not UUID_RE.match(trade_id):
        raise HTTPException(status_code=400, detail="Invalid trade ID format")

    result = await db.execute(
        select(Trade).where(Trade.id == trade_id, Trade.user_id == user.id)
    )
    trade = result.scalar_one_or_none()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    await db.delete(trade)
    logger.info("Trade %s deleted by user %s", trade_id, user.email)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_trades(
    confirm: str = Query(..., description="Must pass 'yes' to confirm deletion"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if confirm != "yes":
        raise HTTPException(status_code=400, detail="Pass ?confirm=yes to confirm deletion of all trades")
    await db.execute(delete(Trade).where(Trade.user_id == user.id))
    logger.warning("All trades deleted for user %s", user.email)


@router.get("/export")
async def export_trades(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Trade).where(Trade.user_id == user.id).order_by(Trade.timestamp)
    )
    trades = result.scalars().all()

    lines = ["date,symbol,side,entry_price,exit_price,quantity,pnl,duration,setup,notes,fees"]
    for t in trades:
        lines.append(
            f"{t.timestamp.isoformat()},{t.symbol},{t.side},{t.entry_price},"
            f"{t.exit_price},{t.quantity},{t.pnl},{t.duration_minutes or ''},"
            f"{t.setup_type or ''},{(t.notes or '').replace(',', ';')},{t.fees}"
        )

    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        content="\n".join(lines),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=tradeloop_export.csv"},
    )
