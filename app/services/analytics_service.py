"""
Analytics Service — orchestrates analytics computation and caching.

In-memory cache for now. Will move to Redis when we add it.
Invalidated on trade.uploaded and trade.deleted events.
"""
from __future__ import annotations

import logging
import time
from dataclasses import asdict
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.analytics import TradeAnalytics
from app.engine.counterfactual import CounterfactualEngine
from app.engine.weekly_report import WeeklyReportEngine
from app.models.user import User
from app.services.event_bus import event_bus

logger = logging.getLogger("tradeloop.service.analytics")


class AnalyticsCache:
    """Simple in-memory cache. Replace with Redis later — same interface."""

    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, float] = {}
        self._ttl = 300  # 5 minutes

    def get(self, user_id: str, key: str) -> Optional[Any]:
        cache_key = f"{user_id}:{key}"
        if cache_key not in self._store:
            return None
        if time.time() - self._timestamps.get(cache_key, 0) > self._ttl:
            del self._store[cache_key]
            return None
        return self._store[cache_key]

    def set(self, user_id: str, key: str, value: Any) -> None:
        cache_key = f"{user_id}:{key}"
        self._store[cache_key] = value
        self._timestamps[cache_key] = time.time()

    def invalidate(self, user_id: str) -> None:
        keys_to_remove = [k for k in self._store if k.startswith(f"{user_id}:")]
        for k in keys_to_remove:
            del self._store[k]
            self._timestamps.pop(k, None)
        if keys_to_remove:
            logger.info("Cache invalidated for user %s (%d keys)", user_id, len(keys_to_remove))


# Singleton cache
_cache = AnalyticsCache()


class AnalyticsService:

    def __init__(self) -> None:
        self._analytics = TradeAnalytics()
        self._counterfactual = CounterfactualEngine()
        self._weekly = WeeklyReportEngine()
        self._register_event_handlers()

    def _register_event_handlers(self) -> None:
        event_bus.on("trade.uploaded", self._on_trade_change)
        event_bus.on("trade.deleted", self._on_trade_change)

    async def _on_trade_change(self, user_id: str, **kwargs: Any) -> None:
        _cache.invalidate(user_id)

    async def get_full_analytics(
        self, trades: list, user: User, tz_offset: int = 0
    ) -> dict:
        cached = _cache.get(user.id, f"full:{tz_offset}")
        if cached is not None:
            logger.info("Cache hit for full analytics: %s", user.email)
            return cached

        if len(trades) > 10000:
            logger.warning(
                "User %s has %d trades — analytics computation may use significant memory",
                user.email, len(trades),
            )

        t0 = time.time()
        try:
            result = self._analytics.compute_all(trades, tz_offset_hours=tz_offset)
            data = asdict(result)
        except Exception:
            logger.exception("compute_all FAILED for user %s (%d trades)", user.email, len(trades))
            data = asdict(self._analytics.__class__().compute_all([]))
        elapsed = round((time.time() - t0) * 1000, 1)
        logger.info("Full analytics computed for %s (%d trades, %sms)", user.email, len(trades), elapsed)

        _cache.set(user.id, f"full:{tz_offset}", data)
        return data

    async def get_overview(self, trades: list, tz_offset: int = 0) -> dict:
        return self._analytics.overall_metrics(trades, tz_offset_hours=tz_offset)

    async def get_time_analysis(self, trades: list, tz_offset: int = 0) -> dict:
        return self._analytics.time_analysis(trades, tz_offset_hours=tz_offset)

    async def get_behavior(self, trades: list, tz_offset: int = 0) -> dict:
        return self._analytics.behavioral_analysis(trades, tz_offset_hours=tz_offset)

    async def get_symbols(self, trades: list) -> dict:
        return self._analytics.symbol_analysis(trades)

    async def get_equity_curve(self, trades: list, tz_offset: int = 0) -> dict:
        return self._analytics.equity_curve_data(trades, tz_offset_hours=tz_offset)

    async def get_risk_metrics(self, trades: list, tz_offset: int = 0) -> dict:
        return self._analytics.risk_metrics(trades, tz_offset_hours=tz_offset)

    async def get_streaks(self, trades: list) -> dict:
        return self._analytics.streak_analysis(trades)

    async def get_insights(
        self, trades: list, user: User, tz_offset: int = 0
    ) -> dict:
        cached = _cache.get(user.id, f"insights:{tz_offset}")
        if cached is not None:
            logger.info("Cache hit for insights: %s", user.email)
            return cached

        t0 = time.time()
        result = self._counterfactual.analyze(trades, tz_offset_hours=tz_offset)
        elapsed = round((time.time() - t0) * 1000, 1)
        logger.info("Insights computed for %s (%d trades, %sms)", user.email, len(trades), elapsed)

        _cache.set(user.id, f"insights:{tz_offset}", result)
        return result

    async def get_weekly_report(
        self, trades: list, tz_offset: int = 0, week_end_date: Any = None
    ) -> dict:
        return self._weekly.generate(trades, tz_offset_hours=tz_offset, week_end_date=week_end_date)
