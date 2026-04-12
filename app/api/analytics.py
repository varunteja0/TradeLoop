"""Analytics API — thin routes, all logic in AnalyticsService."""
from __future__ import annotations

from datetime import datetime, timezone as tz_mod
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.trade import AnalyticsResponse
from app.services import analytics_svc as analytics_service, trade_svc as trade_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _tz(user: User, tz: int = None) -> int:
    return tz if tz is not None else user.timezone_offset


@router.get("/full")
async def full_analytics(
    tz: int = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trades = await trade_service.get_user_trades(db, user)
    tz_val = _tz(user, tz)

    if from_date:
        try:
            from_dt = datetime.fromisoformat(from_date).replace(tzinfo=tz_mod.utc)
            trades = [t for t in trades if t.timestamp and t.timestamp >= from_dt]
        except ValueError:
            pass
    if to_date:
        try:
            to_dt = datetime.fromisoformat(to_date).replace(tzinfo=tz_mod.utc)
            trades = [t for t in trades if t.timestamp and t.timestamp <= to_dt]
        except ValueError:
            pass

    from app.engine.analytics import TradeAnalytics
    ta = TradeAnalytics()
    overview = ta.overall_metrics(trades, tz_offset_hours=tz_val)
    time_analysis = ta.time_analysis(trades, tz_offset_hours=tz_val)
    behavioral = ta.behavioral_analysis(trades, tz_offset_hours=tz_val)
    symbols = ta.symbol_analysis(trades)
    streaks = ta.streak_analysis(trades)
    equity_curve = ta.equity_curve_data(trades, tz_offset_hours=tz_val)
    risk_metrics = ta.risk_metrics(trades, tz_offset_hours=tz_val)

    return {
        "overview": overview,
        "time_analysis": time_analysis,
        "behavioral": behavioral,
        "symbols": symbols,
        "streaks": streaks,
        "equity_curve": equity_curve,
        "risk_metrics": risk_metrics,
    }


@router.get("/overview")
async def overview(tz: int = Query(None), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    trades = await trade_service.get_user_trades(db, user, limit=10000)
    return await analytics_service.get_overview(trades, _tz(user, tz))


@router.get("/time")
async def time_analysis(tz: int = Query(None), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    trades = await trade_service.get_user_trades(db, user, limit=10000)
    return await analytics_service.get_time_analysis(trades, _tz(user, tz))


@router.get("/behavior")
async def behavior_analysis(tz: int = Query(None), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    trades = await trade_service.get_user_trades(db, user, limit=10000)
    return await analytics_service.get_behavior(trades, _tz(user, tz))


@router.get("/symbols")
async def symbol_analysis(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    trades = await trade_service.get_user_trades(db, user, limit=10000)
    return await analytics_service.get_symbols(trades)


@router.get("/equity-curve")
async def equity_curve(tz: int = Query(None), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    trades = await trade_service.get_user_trades(db, user, limit=10000)
    return await analytics_service.get_equity_curve(trades, _tz(user, tz))


@router.get("/risk")
async def risk_metrics(tz: int = Query(None), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    trades = await trade_service.get_user_trades(db, user, limit=10000)
    return await analytics_service.get_risk_metrics(trades, _tz(user, tz))


@router.get("/streaks")
async def streaks(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    trades = await trade_service.get_user_trades(db, user, limit=10000)
    return await analytics_service.get_streaks(trades)


@router.get("/emotions")
async def emotion_analysis(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    trades = await trade_service.get_user_trades(db, user, limit=10000)
    return analytics_service._analytics.emotion_analysis(trades)
