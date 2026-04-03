"""
Background task functions for FastAPI BackgroundTasks.

These run AFTER the response is sent to the client — they do not
block the request. Called via BackgroundTasks.add_task() in route handlers.

When we outgrow in-process tasks, swap to ARQ (async Redis queue) with
the same function signatures. The interface stays identical.
"""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import async_session
from app.models.trade import Trade
from app.models.user import User

logger = logging.getLogger("tradeloop.background")


async def precompute_analytics(user_id: str) -> None:
    """Precompute and cache analytics for a user after trade changes."""
    from app.services import analytics_svc

    async with async_session() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return

        trades_result = await db.execute(
            select(Trade).where(Trade.user_id == user_id).order_by(Trade.timestamp)
        )
        trades = list(trades_result.scalars().all())

        await analytics_svc.get_full_analytics(trades, user, user.timezone_offset)
        await analytics_svc.get_insights(trades, user, user.timezone_offset)
        logger.info("Background precompute complete for user %s (%d trades)", user.email, len(trades))


async def check_all_compliance(user_id: str) -> None:
    """Check compliance for all prop accounts after trade changes."""
    from app.services import compliance_svc
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

        for account in accounts:
            try:
                report = await compliance_svc.check_compliance(db, user, account)
                if report.overall_status in ("critical", "violated"):
                    logger.warning(
                        "Compliance alert for %s account %s: %s",
                        user.email, account.name, report.overall_status,
                    )
            except Exception:
                logger.exception("Compliance check failed for account %s", account.id)

        await db.commit()


async def run_post_upload(user_id: str) -> None:
    """Run precompute + compliance AFTER the response is sent."""
    try:
        await precompute_analytics(user_id)
        await check_all_compliance(user_id)
    except Exception:
        logger.exception("Post-upload background work failed for user %s", user_id)
