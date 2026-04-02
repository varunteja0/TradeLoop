from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class TradeCreate(BaseModel):
    timestamp: datetime
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    duration_minutes: Optional[float] = None
    setup_type: Optional[str] = None
    notes: Optional[str] = None
    fees: float = 0.0


class TradeOut(BaseModel):
    id: str
    timestamp: datetime
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    duration_minutes: Optional[float]
    setup_type: Optional[str]
    notes: Optional[str]
    fees: float

    model_config = {"from_attributes": True}


class TradeListResponse(BaseModel):
    trades: List[TradeOut]
    total: int
    page: int
    per_page: int


class UploadResponse(BaseModel):
    imported: int
    skipped: int
    errors: List[str]


class AnalyticsResponse(BaseModel):
    overview: dict
    time_analysis: dict
    behavioral: dict
    symbols: dict
    streaks: dict
    equity_curve: dict
    risk_metrics: dict
