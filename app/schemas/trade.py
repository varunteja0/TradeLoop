from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

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
    mood: Optional[str] = None


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
    mood: Optional[str] = None

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
    overview: Dict[str, Any]
    time_analysis: Dict[str, Any]
    behavioral: Dict[str, Any]
    symbols: Dict[str, Any]
    streaks: Dict[str, Any]
    equity_curve: Dict[str, Any]
    risk_metrics: Dict[str, Any]
