from __future__ import annotations

import logging
from dataclasses import asdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.dependencies import get_current_user
from app.models.trade import Trade
from app.models.user import User
from app.engine.analytics import TradeAnalytics
from app.schemas.trade import AnalyticsResponse

logger = logging.getLogger("tradeloop.analytics")
router = APIRouter(prefix="/analytics", tags=["analytics"])

engine = TradeAnalytics()


async def _get_user_trades(db: AsyncSession, user: User) -> list:
    result = await db.execute(
        select(Trade).where(Trade.user_id == user.id).order_by(Trade.timestamp)
    )
    return list(result.scalars().all())


def _get_tz(user: User, tz_override: int = None) -> int:
    if tz_override is not None:
        return tz_override
    return user.timezone_offset


@router.get("/full", response_model=AnalyticsResponse)
async def full_analytics(
    tz: int = Query(None, description="Timezone offset in hours (overrides profile setting)"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trades = await _get_user_trades(db, user)
    tz_offset = _get_tz(user, tz)
    analytics = engine.compute_all(trades, tz_offset_hours=tz_offset)
    logger.info("Full analytics computed for %s (%d trades)", user.email, len(trades))
    return AnalyticsResponse(**asdict(analytics))


@router.get("/overview")
async def overview(
    tz: int = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trades = await _get_user_trades(db, user)
    return engine.overall_metrics(trades, tz_offset_hours=_get_tz(user, tz))


@router.get("/time")
async def time_analysis(
    tz: int = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trades = await _get_user_trades(db, user)
    return engine.time_analysis(trades, tz_offset_hours=_get_tz(user, tz))


@router.get("/behavior")
async def behavior_analysis(
    tz: int = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trades = await _get_user_trades(db, user)
    return engine.behavioral_analysis(trades, tz_offset_hours=_get_tz(user, tz))


@router.get("/symbols")
async def symbol_analysis(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trades = await _get_user_trades(db, user)
    return engine.symbol_analysis(trades)


@router.get("/equity-curve")
async def equity_curve(
    tz: int = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trades = await _get_user_trades(db, user)
    return engine.equity_curve_data(trades, tz_offset_hours=_get_tz(user, tz))


@router.get("/risk")
async def risk_metrics(
    tz: int = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trades = await _get_user_trades(db, user)
    return engine.risk_metrics(trades, tz_offset_hours=_get_tz(user, tz))


@router.get("/streaks")
async def streaks(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trades = await _get_user_trades(db, user)
    return engine.streak_analysis(trades)
