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


@router.get("/export")
async def export_trades(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    csv_content = await trade_service.export_csv(db, user)
    return PlainTextResponse(
        content=csv_content, media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=tradeloop_export.csv"},
    )
