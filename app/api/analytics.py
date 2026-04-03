"""Analytics API — thin routes, all logic in AnalyticsService."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.trade import AnalyticsResponse
from app.services.analytics_service import AnalyticsService
from app.services.trade_service import TradeService

router = APIRouter(prefix="/analytics", tags=["analytics"])
analytics_service = AnalyticsService()
trade_service = TradeService()


def _tz(user: User, tz: int = None) -> int:
    return tz if tz is not None else user.timezone_offset


@router.get("/full", response_model=AnalyticsResponse)
async def full_analytics(
    tz: int = Query(None), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    trades = await trade_service.get_user_trades(db, user, limit=10000)
    return await analytics_service.get_full_analytics(trades, user, _tz(user, tz))


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
