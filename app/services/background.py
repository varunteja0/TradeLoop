"""
Background task system using FastAPI's BackgroundTasks.

For a small team, this is the right choice — no Redis/Celery dependency.
When we outgrow in-process tasks, swap to ARQ (async Redis queue) with
the same function signatures. The interface stays identical.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import async_session
from app.models.trade import Trade
from app.models.user import User
from app.services.event_bus import event_bus

logger = logging.getLogger("tradeloop.background")


async def precompute_analytics(user_id: str) -> None:
    """Precompute and cache analytics for a user after trade changes."""
    from app.services.analytics_service import AnalyticsService

    async with async_session() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return

        trades_result = await db.execute(
            select(Trade).where(Trade.user_id == user_id).order_by(Trade.timestamp)
        )
        trades = list(trades_result.scalars().all())

        service = AnalyticsService()
        await service.get_full_analytics(trades, user, user.timezone_offset)
        await service.get_insights(trades, user, user.timezone_offset)
        logger.info("Background precompute complete for user %s (%d trades)", user.email, len(trades))


async def check_all_compliance(user_id: str) -> None:
    """Check compliance for all prop accounts after trade changes."""
    from app.services.compliance_service import ComplianceService
    from app.models.prop_account import PropAccount

    async with async_session() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return

        accounts_result = await db.execute(
            select(PropAccount).where(PropAccount.user_id == user_id, PropAccount.is_active == True)
        )
        accounts = accounts_result.scalars().all()

        if not accounts:
            return

        service = ComplianceService()
        for account in accounts:
            try:
                report = await service.check_compliance(db, user, account)
                if report.overall_status in ("critical", "violated"):
                    logger.warning(
                        "Compliance alert for %s account %s: %s",
                        user.email, account.name, report.overall_status,
                    )
            except Exception:
                logger.exception("Compliance check failed for account %s", account.id)

        await db.commit()


async def run_post_upload(user_id: str) -> None:
    """Run precompute + compliance outside the request cycle via BackgroundTasks."""
    try:
        await precompute_analytics(user_id)
        await check_all_compliance(user_id)
    except Exception:
        logger.exception("Post-upload background work failed for user %s", user_id)


def register_background_handlers() -> None:
    """Wire event handlers that trigger background work."""

    async def on_trade_change(user_id: str, **kwargs: Any) -> None:
        await precompute_analytics(user_id)
        await check_all_compliance(user_id)

    event_bus.on("trade.uploaded", on_trade_change)
    event_bus.on("trade.synced", on_trade_change)
    logger.info("Background handlers registered")
