"""Trade API — thin routes, all logic in TradeService."""
from __future__ import annotations

import re
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, UploadFile, File, Query, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db
from app.dependencies import get_current_user
from app.rate_limit import limiter
from app.models.user import User
from app.schemas.trade import TradeOut, TradeListResponse, UploadResponse
from app.services.background import run_post_upload
from app.services import trade_svc as trade_service

router = APIRouter(prefix="/trades", tags=["trades"])
settings = get_settings()
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)


@router.post("/upload", response_model=UploadResponse)
@limiter.limit("10/minute")
async def upload_csv(
    request: Request,
    file: UploadFile = File(...),
    broker: str = Query("auto"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")

    raw = await file.read()
    if len(raw) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 5MB.")

    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding not supported. Please use UTF-8.")

    try:
        result = await trade_service.upload_csv(db, user, content, broker)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    background_tasks.add_task(run_post_upload, user.id)

    return UploadResponse(imported=result.imported, skipped=result.skipped, errors=result.errors)


@router.get("", response_model=TradeListResponse)
async def list_trades(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    symbol: Optional[str] = Query(None),
    side: Optional[str] = Query(None),
    sort_by: str = Query("timestamp"),
    sort_dir: str = Query("desc"),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await trade_service.list_trades(db, user, page, per_page, symbol, side, sort_by, sort_dir, search)
    total_pages = max(1, (result.total + per_page - 1) // per_page)
    return TradeListResponse(
        trades=[TradeOut(id=str(t.id), **{k: getattr(t, k) for k in TradeOut.model_fields if k != "id"}) for t in result.trades],
        total=result.total, page=result.page, per_page=result.per_page,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@router.get("/symbols")
async def list_symbols(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await trade_service.list_symbols(db, user)


@router.delete("/{trade_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trade(trade_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if not UUID_RE.match(trade_id):
        raise HTTPException(status_code=400, detail="Invalid trade ID format")
    try:
        await trade_service.delete_trade(db, user, trade_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Trade not found")


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_trades(
    confirm: str = Query(...), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    if confirm != "yes":
        raise HTTPException(status_code=400, detail="Pass ?confirm=yes to confirm deletion of all trades")
    await trade_service.delete_all_trades(db, user)


@router.patch("/{trade_id}")
async def update_trade(trade_id: str, body: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        await trade_service.update_trade(db, user, trade_id, body)
    except LookupError:
        raise HTTPException(status_code=404, detail="Trade not found")
    return {"status": "updated", "trade_id": trade_id}


@router.post("/load-sample")
async def load_sample_data(
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Load sample trades so users can explore the dashboard immediately."""
    import os
    sample_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "sample_trades.csv")
    if not os.path.exists(sample_path):
        raise HTTPException(status_code=404, detail="Sample data not available")

    with open(sample_path, "r") as f:
        content = f.read()

    try:
        result = await trade_service.upload_csv(db, user, content, broker="auto")
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    background_tasks.add_task(run_post_upload, user.id)
    return {"status": "ok", "imported": result.imported, "message": f"Loaded {result.imported} sample trades. Explore your dashboard!"}


@router.post("/generate-synthetic")
async def generate_synthetic(
    scenario: str = Query("mixed"),
    count: int = Query(50, ge=10, le=500),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generate synthetic trades with realistic behavioral patterns for demos/testing."""
    from app.engine.synthetic import synthetic_generator
    from app.models.trade import Trade as TradeModel

    valid_scenarios = {"mixed", "revenge_heavy", "overtrading", "disciplined",
                       "losing_streak", "risk_mismanagement", "improving"}
    if scenario not in valid_scenarios:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scenario. Must be one of: {', '.join(sorted(valid_scenarios))}",
        )

    remaining = await trade_service._check_free_tier(db, user)
    if remaining is not None:
        count = min(count, remaining)

    synthetic_trades = synthetic_generator.generate(scenario=scenario, num_trades=count)

    imported = 0
    for td in synthetic_trades:
        trade = TradeModel(
            user_id=user.id,
            timestamp=td.timestamp,
            symbol=td.symbol,
            side=td.side,
            entry_price=td.entry_price,
            exit_price=td.exit_price,
            quantity=td.quantity,
            pnl=td.pnl,
            duration_minutes=td.duration_minutes,
            setup_type=td.setup_type,
            fees=td.fees,
            mood=td.mood,
            mistake_category=td.mistake_category,
            source="synthetic",
        )
        db.add(trade)
        imported += 1

    await db.flush()
    background_tasks.add_task(run_post_upload, user.id)

    return {
        "status": "ok",
        "scenario": scenario,
        "imported": imported,
        "message": f"Generated {imported} synthetic trades ({scenario} scenario). Check your dashboard!",
    }


@router.get("/export")
async def export_trades(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    csv_content = await trade_service.export_csv(db, user)

    from datetime import datetime, timezone
    user.last_export_at = datetime.now(timezone.utc)
    await db.flush()

    return PlainTextResponse(
        content=csv_content, media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=tradeloop_export.csv"},
    )


@router.get("/backup-status")
async def backup_status(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """Check backup status — nudge users to export if they haven't recently."""
    from datetime import datetime, timezone
    from sqlalchemy import func, select
    from app.models.trade import Trade as TradeModel

    count_result = await db.execute(
        select(func.count()).select_from(TradeModel).where(TradeModel.user_id == user.id)
    )
    trade_count = count_result.scalar() or 0

    last_export = user.last_export_at
    now = datetime.now(timezone.utc)

    needs_backup = False
    days_since_export = None

    if last_export:
        last_naive = last_export.replace(tzinfo=None) if last_export.tzinfo else last_export
        now_naive = now.replace(tzinfo=None)
        days_since_export = (now_naive - last_naive).days
        needs_backup = days_since_export >= 7 and trade_count > 0
    elif trade_count > 0:
        needs_backup = True

    return {
        "trade_count": trade_count,
        "last_export_at": last_export.isoformat() if last_export else None,
        "days_since_export": days_since_export,
        "needs_backup": needs_backup,
        "message": (
            "You haven't exported your trades in a while. Back up now to keep your data safe."
            if needs_backup
            else "Your data backup is up to date." if last_export
            else "No trades to back up yet."
        ),
    }
