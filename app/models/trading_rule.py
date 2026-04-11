from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Float, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _new_uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TradingRule(Base):
    """
    User-defined trading rules.

    Supported rule types:
      - max_trades_per_day: no more than N trades per calendar day
      - max_loss_per_day: stop trading after losing X in a day
      - max_loss_per_trade: no single trade should lose more than X
      - no_trading_after: stop trading after a given hour (24h format)
      - no_trading_before: don't trade before a given hour
      - max_consecutive_losses: stop after N consecutive losses
      - min_rr_ratio: minimum risk:reward ratio
      - max_position_size: max quantity per trade

    Each rule has a type and a numeric threshold. The engine checks
    each trade against the user's active rules.
    """
    __tablename__ = "trading_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    label: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(), default=_utcnow, onupdate=_utcnow)
