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


async def auto_tag_trades(user_id: str) -> None:
    """Run rules-based auto-tagging on trades missing mood/mistake tags."""
    from app.engine.auto_tagger import auto_tagger

    async with async_session() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return

        trades_result = await db.execute(
            select(Trade).where(Trade.user_id == user_id).order_by(Trade.timestamp)
        )
        trades = list(trades_result.scalars().all())
        if len(trades) < 2:
            return

        updates = auto_tagger.tag_trades(trades)
        if not updates:
            return

        trade_map = {t.id: t for t in trades}
        for trade_id, changes in updates:
            trade = trade_map.get(trade_id)
            if trade:
                for key, value in changes.items():
                    setattr(trade, key, value)

        await db.commit()
        logger.info("Auto-tagged %d trades for user %s", len(updates), user.email)


async def check_trading_rules(user_id: str) -> None:
    """Check all user-defined trading rules and store violations."""
    from app.engine.rule_checker import rule_checker
    from app.models.trading_rule import TradingRule
    from app.models.rule_violation import RuleViolation

    async with async_session() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return

        rules_result = await db.execute(
            select(TradingRule).where(TradingRule.user_id == user_id, TradingRule.is_active == True)
        )
        rules = list(rules_result.scalars().all())
        if not rules:
            return

        trades_result = await db.execute(
            select(Trade).where(Trade.user_id == user_id).order_by(Trade.timestamp)
        )
        trades = list(trades_result.scalars().all())
        if not trades:
            return

        violations = rule_checker.check_all(trades, rules, user.timezone_offset)
        if not violations:
            return

        existing_result = await db.execute(
            select(RuleViolation.trade_id, RuleViolation.rule_id)
            .where(RuleViolation.user_id == user_id)
        )
        existing = {(row[0], row[1]) for row in existing_result.all()}

        new_count = 0
        for v in violations:
            trade_id = v.trade.id if v.trade else None
            key = (trade_id, v.rule.id)
            if key in existing:
                continue

            violation = RuleViolation(
                user_id=user_id,
                rule_id=v.rule.id,
                trade_id=trade_id,
                rule_type=v.rule.rule_type,
                message=v.message,
                severity=v.severity,
            )
            db.add(violation)
            new_count += 1

        if new_count > 0:
            await db.commit()
            logger.info("Found %d new rule violations for user %s", new_count, user.email)


async def run_post_upload(user_id: str) -> None:
    """Run auto-tag + rules + precompute + compliance AFTER the response is sent."""
    try:
        await auto_tag_trades(user_id)
        await check_trading_rules(user_id)
        await precompute_analytics(user_id)
        await check_all_compliance(user_id)
    except Exception:
        logger.exception("Post-upload background work failed for user %s", user_id)
