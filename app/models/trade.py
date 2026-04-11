from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Float, DateTime, ForeignKey, Text, Index, CheckConstraint, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _new_uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Trade(Base):
    __tablename__ = "trades"
    __table_args__ = (
        Index("ix_trades_user_timestamp", "user_id", "timestamp"),
        Index("ix_trades_timestamp", "timestamp"),
        CheckConstraint("side IN ('BUY', 'SELL')", name="ck_trade_side"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(), nullable=False)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    side: Mapped[str] = mapped_column(String(10), nullable=False)
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    exit_price: Mapped[float] = mapped_column(Float, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    pnl: Mapped[float] = mapped_column(Float, nullable=False)
    duration_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    setup_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fees: Mapped[float] = mapped_column(Float, default=0.0)
    source: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # "csv", "zerodha", "angelone"
    mood: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)  # "confident", "fearful", "revenge", "fomo", "bored", "calm"
    reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # why the trade was taken
    rule_followed: Mapped[Optional[bool]] = mapped_column(nullable=True)  # did the trader follow their rules?
    mistake_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # "early_exit", "no_stop_loss", "oversized", "fomo_entry", "revenge", "none"
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(), default=_utcnow, onupdate=_utcnow)

    user = relationship("User", back_populates="trades")
