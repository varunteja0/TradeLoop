from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.dependencies import get_current_user
from app.models.trade import Trade
from app.models.user import User
from app.engine.analytics import TradeAnalytics
from app.schemas.trade import AnalyticsResponse

router = APIRouter(prefix="/analytics", tags=["analytics"])

engine = TradeAnalytics()


async def _get_user_trades(db: AsyncSession, user: User) -> list[Trade]:
    result = await db.execute(
        select(Trade).where(Trade.user_id == user.id).order_by(Trade.timestamp)
    )
    return list(result.scalars().all())


@router.get("/full", response_model=AnalyticsResponse)
async def full_analytics(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trades = await _get_user_trades(db, user)
    analytics = engine.compute_all(trades)
    return AnalyticsResponse(**asdict(analytics))


@router.get("/overview")
async def overview(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trades = await _get_user_trades(db, user)
    return engine.overall_metrics(trades)


@router.get("/time")
async def time_analysis(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trades = await _get_user_trades(db, user)
    return engine.time_analysis(trades)


@router.get("/behavior")
async def behavior_analysis(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trades = await _get_user_trades(db, user)
    return engine.behavioral_analysis(trades)


@router.get("/symbols")
async def symbol_analysis(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trades = await _get_user_trades(db, user)
    return engine.symbol_analysis(trades)


@router.get("/equity-curve")
async def equity_curve(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trades = await _get_user_trades(db, user)
    return engine.equity_curve_data(trades)


@router.get("/risk")
async def risk_metrics(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trades = await _get_user_trades(db, user)
    return engine.risk_metrics(trades)


@router.get("/streaks")
async def streaks(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trades = await _get_user_trades(db, user)
    return engine.streak_analysis(trades)
