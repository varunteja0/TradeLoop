from __future__ import annotations
import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.dependencies import get_current_user
from app.models.trade import Trade
from app.models.user import User
from app.engine.counterfactual import CounterfactualEngine

logger = logging.getLogger("tradeloop.insights")
router = APIRouter(prefix="/insights", tags=["insights"])
engine = CounterfactualEngine()

@router.get("/full")
async def full_insights(
    tz: int = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Trade).where(Trade.user_id == user.id).order_by(Trade.timestamp)
    )
    trades = list(result.scalars().all())
    tz_offset = tz if tz is not None else user.timezone_offset
    insights = engine.analyze(trades, tz_offset_hours=tz_offset)
    logger.info("Insights computed for %s (%d trades, %d insights)", user.email, len(trades), len(insights.get("insights", [])))
    return insights
