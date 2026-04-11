from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _new_uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RuleViolation(Base):
    """
    Record of a rule being violated by a specific trade.
    Links a TradingRule to a Trade with a human-readable message.
    """
    __tablename__ = "rule_violations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    rule_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("trading_rules.id", ondelete="CASCADE"), nullable=False
    )
    trade_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("trades.id", ondelete="SET NULL"), nullable=True
    )
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="warning")  # "info", "warning", "critical"
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=_utcnow)
