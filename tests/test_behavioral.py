from __future__ import annotations

from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from typing import List

import pytest

from app.engine.behavioral import BehavioralAnalyzer
from tests.conftest import make_trade

analyzer = BehavioralAnalyzer()

BASE_TS = datetime(2024, 6, 10, 9, 0, 0, tzinfo=timezone.utc)  # Monday


# =====================================================================
# Revenge trading
# =====================================================================
class TestRevengeTrades:

    def test_revenge_trades_detected(self):
        """Loss followed by a trade 2 minutes later counts as revenge."""
        trades = [
            make_trade(pnl=-100, timestamp=BASE_TS),
            make_trade(pnl=50, timestamp=BASE_TS + timedelta(minutes=2)),
            make_trade(pnl=80, timestamp=BASE_TS + timedelta(hours=1)),
            make_trade(pnl=-30, timestamp=BASE_TS + timedelta(hours=2)),
            make_trade(pnl=60, timestamp=BASE_TS + timedelta(hours=2, minutes=1)),
        ]
        result = analyzer._revenge_trades(trades)
        assert result["count"] == 2

    def test_revenge_trades_none(self):
        """Well-spaced trades (>5 min apart) should not be flagged."""
        trades = [
            make_trade(pnl=-100, timestamp=BASE_TS),
            make_trade(pnl=50, timestamp=BASE_TS + timedelta(minutes=10)),
            make_trade(pnl=-80, timestamp=BASE_TS + timedelta(minutes=30)),
            make_trade(pnl=60, timestamp=BASE_TS + timedelta(hours=1)),
            make_trade(pnl=40, timestamp=BASE_TS + timedelta(hours=2)),
        ]
        result = analyzer._revenge_trades(trades)
        assert result["count"] == 0
        assert result["win_rate"] is None


# =====================================================================
# Overtrading
# =====================================================================
class TestOvertrading:

    def test_overtrading_detection(self):
        """Day with 20 trades vs days with 2 should be flagged."""
        trades = []
        # Day 1: 2 trades
        for i in range(2):
            trades.append(make_trade(
                pnl=50, timestamp=BASE_TS + timedelta(hours=i),
            ))
        # Day 2: 2 trades
        for i in range(2):
            trades.append(make_trade(
                pnl=-30, timestamp=BASE_TS + timedelta(days=1, hours=i),
            ))
        # Day 3: 20 trades — this should be flagged
        for i in range(20):
            trades.append(make_trade(
                pnl=-10, timestamp=BASE_TS + timedelta(days=2, minutes=i * 15),
            ))

        result = analyzer._overtrading_days(trades)
        assert result["count"] >= 1
        flagged_dates = [d["date"] for d in result["days"]]
        heavy_day = (BASE_TS + timedelta(days=2)).date().isoformat()
        assert heavy_day in flagged_dates


# =====================================================================
# Tilt detection
# =====================================================================
class TestTiltDetection:

    def test_tilt_detection(self):
        """2 consecutive losses then a size increase >20% triggers tilt."""
        trades = [
            make_trade(pnl=-100, quantity=10, timestamp=BASE_TS),
            make_trade(pnl=-80, quantity=10, timestamp=BASE_TS + timedelta(hours=1)),
            make_trade(pnl=-50, quantity=15, timestamp=BASE_TS + timedelta(hours=2)),  # 50% increase
            make_trade(pnl=200, quantity=10, timestamp=BASE_TS + timedelta(hours=3)),
            make_trade(pnl=100, quantity=10, timestamp=BASE_TS + timedelta(hours=4)),
        ]
        result = analyzer._tilt_detection(trades)
        assert result["tilt_events"] >= 1
        assert result["events"][0]["size_increase_pct"] == 50.0


# =====================================================================
# Streak behavior
# =====================================================================
class TestStreakBehavior:

    def test_streak_behavior(self):
        """4 wins then a loss — 1 occurrence of win streak >= 3, check next trade stats."""
        trades = [
            make_trade(pnl=100, timestamp=BASE_TS + timedelta(hours=i))
            for i in range(4)
        ] + [
            make_trade(pnl=-50, timestamp=BASE_TS + timedelta(hours=4)),
        ]

        result = analyzer._streak_behavior(trades, streak_type="win", min_streak=3)
        assert result["occurrences"] == 1
        assert result["next_trade_win_rate"] == 0.0
        assert result["next_trade_avg_pnl"] == -50.0


# =====================================================================
# Insufficient data
# =====================================================================
class TestInsufficientData:

    def test_insufficient_data(self):
        trades = [
            make_trade(pnl=100, timestamp=BASE_TS + timedelta(hours=i))
            for i in range(4)
        ]
        result = analyzer.analyze(trades)
        assert result["insufficient_data"] is True
        assert result["min_trades_needed"] == 5


# =====================================================================
# Day effect
# =====================================================================
class TestDayEffect:

    def test_day_effect_significance(self):
        """Strong Friday underperformance with enough sample size."""
        trades = []
        # 10 winning trades on non-Fridays (Monday–Thursday)
        for i in range(10):
            day_offset = i % 4  # Mon=0, Tue=1, Wed=2, Thu=3
            ts = datetime(2024, 6, 10 + day_offset, 10, 0, tzinfo=timezone.utc)
            trades.append(make_trade(pnl=100, timestamp=ts))

        # 7 losing trades on Fridays (need >= 5 for significance)
        for i in range(7):
            ts = datetime(2024, 6, 14, 10 + i, 0, tzinfo=timezone.utc)  # Friday
            trades.append(make_trade(pnl=-80, timestamp=ts))

        result = analyzer._day_effect(trades, target_day=4, label="Friday")
        assert result["has_data"] is True
        assert result["is_significant"] is True
        assert result["difference"] < 0  # Friday worse than others
        assert result["trades"] == 7
        assert result["win_rate"] == 0.0
