from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.dependencies import get_current_user
from app.models.trade import Trade
from app.models.user import User
from app.schemas.trade import TradeOut, TradeListResponse, UploadResponse
from app.engine.csv_parser import parse_csv

router = APIRouter(prefix="/trades", tags=["trades"])


@router.post("/upload", response_model=UploadResponse)
async def upload_csv(
    file: UploadFile = File(...),
    broker: str = Query("auto", description="Broker format: auto, generic, zerodha, mt4"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")

    content = (await file.read()).decode("utf-8-sig")
    parsed = parse_csv(content, broker=broker)

    if not parsed:
        raise HTTPException(status_code=400, detail="No valid trades found in the CSV. Check your file format.")

    imported = 0
    skipped = 0
    errors = []

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
    return UploadResponse(imported=imported, skipped=skipped, errors=errors[:5])


@router.get("", response_model=TradeListResponse)
async def list_trades(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    symbol: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(Trade).where(Trade.user_id == user.id)
    count_query = select(func.count()).select_from(Trade).where(Trade.user_id == user.id)

    if symbol:
        query = query.where(Trade.symbol == symbol.upper())
        count_query = count_query.where(Trade.symbol == symbol.upper())

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Trade.timestamp.desc()).offset((page - 1) * per_page).limit(per_page)
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


@router.delete("/{trade_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trade(
    trade_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Trade).where(Trade.id == trade_id, Trade.user_id == user.id)
    )
    trade = result.scalar_one_or_none()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    await db.delete(trade)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_trades(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await db.execute(delete(Trade).where(Trade.user_id == user.id))
