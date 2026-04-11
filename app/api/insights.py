"""Insights API — thin route, logic in AnalyticsService + IntelligenceEngine."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.rule_violation import RuleViolation
from app.engine.intelligence import intelligence_engine
from app.services import analytics_svc as analytics_service, trade_svc as trade_service

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/full")
async def full_insights(
    tz: int = Query(None), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    trades = await trade_service.get_user_trades(db, user)
    tz_offset = tz if tz is not None else user.timezone_offset
    return await analytics_service.get_insights(trades, user, tz_offset)


@router.get("/alerts")
async def intelligence_alerts(
    tz: int = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Personalized behavioral intelligence alerts — TradeLoop's killer feature."""
    trades = await trade_service.get_user_trades(db, user)
    tz_offset = tz if tz is not None else user.timezone_offset

    violations_result = await db.execute(
        select(RuleViolation)
        .where(RuleViolation.user_id == user.id)
        .order_by(RuleViolation.created_at.desc())
        .limit(200)
    )
    violations = list(violations_result.scalars().all())

    return intelligence_engine.generate_alerts(trades, violations, tz_offset)
