from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Float, DateTime, ForeignKey, Integer, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base

def _new_uuid() -> str:
    return str(uuid.uuid4())

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

class PropAccount(Base):
    __tablename__ = "prop_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # "FTMO 100k Challenge #2"
    firm: Mapped[str] = mapped_column(String(50), nullable=False)  # "ftmo", "fundingpips", "custom"
    phase: Mapped[str] = mapped_column(String(30), nullable=False)  # "challenge", "verification", "funded"
    initial_balance: Mapped[float] = mapped_column(Float, nullable=False)
    daily_loss_limit_pct: Mapped[float] = mapped_column(Float, default=5.0)
    max_drawdown_pct: Mapped[float] = mapped_column(Float, default=10.0)
    drawdown_type: Mapped[str] = mapped_column(String(20), default="static")  # "static" or "trailing"
    profit_target_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=10.0)
    min_trading_days: Mapped[int] = mapped_column(Integer, default=10)
    consistency_rule_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(20), default="active")  # "active", "passed", "failed"
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(), default=_utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(), default=_utcnow, onupdate=_utcnow)
