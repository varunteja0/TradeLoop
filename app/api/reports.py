from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.dependencies import get_current_user
from app.models.trade import Trade
from app.models.user import User
from app.engine.weekly_report import WeeklyReportEngine

router = APIRouter(prefix="/reports", tags=["reports"])
report_engine = WeeklyReportEngine()

@router.get("/weekly")
async def weekly_report(
    tz: int = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Trade).where(Trade.user_id == user.id).order_by(Trade.timestamp)
    )
    trades = list(result.scalars().all())
    tz_offset = tz if tz is not None else user.timezone_offset
    return report_engine.generate(trades, tz_offset_hours=tz_offset)
