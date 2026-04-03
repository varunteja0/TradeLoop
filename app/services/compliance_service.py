"""
Compliance Service — prop firm rule tracking.

Manages prop accounts, runs compliance checks, emits warning events.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.prop_rules import PropComplianceEngine, FIRM_PRESETS
from app.models.prop_account import PropAccount
from app.models.trade import Trade
from app.models.user import User
from app.services.event_bus import event_bus

logger = logging.getLogger("tradeloop.service.compliance")


class ComplianceService:

    def __init__(self) -> None:
        self._engine = PropComplianceEngine()
        event_bus.on("trade.uploaded", self._on_trade_change)

    async def _on_trade_change(self, user_id: str, **kwargs: Any) -> None:
        logger.info("Trade change detected for user %s — compliance will be rechecked on next request", user_id)

    def get_presets(self) -> Dict[str, Any]:
        return FIRM_PRESETS

    async def create_account(
        self,
        db: AsyncSession,
        user: User,
        name: str,
        firm: str,
        phase: str,
        initial_balance: float,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> PropAccount:
        preset = FIRM_PRESETS.get(firm, {}).get(phase, {})
        ov = overrides or {}

        account = PropAccount(
            user_id=user.id,
            name=name,
            firm=firm,
            phase=phase,
            initial_balance=initial_balance,
            daily_loss_limit_pct=ov.get("daily_loss_limit_pct") or preset.get("daily_loss_limit_pct", 5.0),
            max_drawdown_pct=ov.get("max_drawdown_pct") or preset.get("max_drawdown_pct", 10.0),
            drawdown_type=ov.get("drawdown_type") or preset.get("drawdown_type", "static"),
            profit_target_pct=ov.get("profit_target_pct") if ov.get("profit_target_pct") is not None else preset.get("profit_target_pct", 10.0),
            min_trading_days=ov.get("min_trading_days") or preset.get("min_trading_days", 10),
            consistency_rule_pct=ov.get("consistency_rule_pct") if ov.get("consistency_rule_pct") is not None else preset.get("consistency_rule_pct"),
        )
        db.add(account)
        await db.flush()
        logger.info("Prop account created: %s for %s", account.name, user.email)
        return account

    async def list_accounts(self, db: AsyncSession, user: User) -> List[PropAccount]:
        result = await db.execute(
            select(PropAccount).where(PropAccount.user_id == user.id)
            .order_by(PropAccount.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_account(self, db: AsyncSession, user: User, account_id: str) -> Optional[PropAccount]:
        result = await db.execute(
            select(PropAccount).where(PropAccount.id == account_id, PropAccount.user_id == user.id)
        )
        return result.scalar_one_or_none()

    async def check_compliance(self, db: AsyncSession, user: User, account: PropAccount) -> dict:
        trades_result = await db.execute(
            select(Trade).where(Trade.user_id == user.id).order_by(Trade.timestamp)
        )
        trades = list(trades_result.scalars().all())

        config = {
            "initial_balance": account.initial_balance,
            "daily_loss_limit_pct": account.daily_loss_limit_pct,
            "max_drawdown_pct": account.max_drawdown_pct,
            "drawdown_type": account.drawdown_type,
            "profit_target_pct": account.profit_target_pct,
            "min_trading_days": account.min_trading_days,
            "consistency_rule_pct": account.consistency_rule_pct,
        }

        report = self._engine.check_compliance(trades, config)

        if report.overall_status == "violated":
            await event_bus.emit("compliance.violated", user_id=user.id, account_id=account.id)
        elif report.overall_status in ("critical", "warning"):
            await event_bus.emit("compliance.warning", user_id=user.id, account_id=account.id, status=report.overall_status)

        return report

    async def delete_account(self, db: AsyncSession, user: User, account_id: str) -> None:
        account = await self.get_account(db, user, account_id)
        if not account:
            raise LookupError("Prop account not found")
        await db.delete(account)
