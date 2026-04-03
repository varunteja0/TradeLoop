"""Reports API — thin route, logic in AnalyticsService."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services import analytics_svc as analytics_service, trade_svc as trade_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/weekly")
async def weekly_report(
    tz: int = Query(None),
    week_of: Optional[str] = Query(None, description="ISO date YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trades = await trade_service.get_user_trades(db, user)
    tz_offset = tz if tz is not None else user.timezone_offset

    week_end = None
    if week_of:
        try:
            week_end = datetime.fromisoformat(week_of).replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    return await analytics_service.get_weekly_report(trades, tz_offset, week_end)
