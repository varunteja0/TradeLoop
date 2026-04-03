from __future__ import annotations

import math
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from typing import List

import pytest

from app.engine.analytics import TradeAnalytics
from tests.conftest import make_trade

engine = TradeAnalytics()

BASE_TS = datetime(2024, 6, 10, 9, 0, 0, tzinfo=timezone.utc)  # Monday


# =====================================================================
# overall_metrics
# =====================================================================
class TestOverallMetrics:

    def test_overall_metrics_basic(self, ten_trades: List[SimpleNamespace]):
        result = engine.overall_metrics(ten_trades)

        assert result["total_trades"] == 10
        assert result["winners"] == 6
        assert result["losers"] == 4
        assert result["win_rate"] == 60.0
        assert result["total_pnl"] == round(6 * 200 + 4 * (-150), 2)  # 600
        assert result["gross_profit"] == 1200.0
        assert result["gross_loss"] == 600.0
        assert result["profit_factor"] == 2.0

    def test_overall_metrics_all_winners(self, all_winners: List[SimpleNamespace]):
        result = engine.overall_metrics(all_winners)

        assert result["win_rate"] == 100.0
        assert result["profit_factor"] is None
        assert result["total_pnl"] > 0
        assert result["losers"] == 0

    def test_overall_metrics_all_losers(self, all_losers: List[SimpleNamespace]):
        result = engine.overall_metrics(all_losers)

        assert result["win_rate"] == 0
        assert result["winners"] == 0
        assert result["total_pnl"] < 0
        assert result["average_winner"] == 0

    def test_overall_metrics_empty(self):
        result = engine.overall_metrics([])
        assert result == {}


# =====================================================================
# time_analysis
# =====================================================================
class TestTimeAnalysis:

    def test_time_analysis_hours(self):
        trades = [
            make_trade(pnl=100, timestamp=datetime(2024, 6, 10, 9, 0, tzinfo=timezone.utc)),
            make_trade(pnl=-50, timestamp=datetime(2024, 6, 10, 9, 30, tzinfo=timezone.utc)),
            make_trade(pnl=200, timestamp=datetime(2024, 6, 10, 14, 0, tzinfo=timezone.utc)),
        ]
        result = engine.time_analysis(trades)

        assert 9 in result["trades_by_hour"]
        assert result["trades_by_hour"][9] == 2
        assert 14 in result["trades_by_hour"]
        assert result["trades_by_hour"][14] == 1
        assert result["win_rate_by_hour"][9] == 50.0
        assert result["win_rate_by_hour"][14] == 100.0

    def test_time_analysis_days(self):
        monday = datetime(2024, 6, 10, 10, 0, tzinfo=timezone.utc)
        wednesday = datetime(2024, 6, 12, 10, 0, tzinfo=timezone.utc)
        trades = [
            make_trade(pnl=100, timestamp=monday),
            make_trade(pnl=-50, timestamp=monday + timedelta(hours=1)),
            make_trade(pnl=200, timestamp=wednesday),
        ]
        result = engine.time_analysis(trades)

        assert result["trades_by_day_of_week"]["Monday"] == 2
        assert result["trades_by_day_of_week"]["Wednesday"] == 1
        assert result["best_day"] == "Wednesday"


# =====================================================================
# symbol_analysis
# =====================================================================
class TestSymbolAnalysis:

    def test_symbol_analysis(self):
        trades = [
            make_trade(pnl=100, symbol="AAPL"),
            make_trade(pnl=-30, symbol="AAPL"),
            make_trade(pnl=200, symbol="TSLA"),
            make_trade(pnl=-50, symbol="MSFT"),
        ]
        result = engine.symbol_analysis(trades)

        assert "AAPL" in result["per_symbol"]
        assert "TSLA" in result["per_symbol"]
        assert "MSFT" in result["per_symbol"]

        aapl = result["per_symbol"]["AAPL"]
        assert aapl["trades"] == 2
        assert aapl["win_rate"] == 50.0
        assert aapl["total_pnl"] == 70.0

        tsla = result["per_symbol"]["TSLA"]
        assert tsla["trades"] == 1
        assert tsla["win_rate"] == 100.0

        assert result["best_symbols"][0]["symbol"] == "TSLA"


# =====================================================================
# streak_analysis
# =====================================================================
class TestStreakAnalysis:

    def test_streak_analysis(self):
        """W W W L L W — max win streak 3, max loss streak 2."""
        trades = [
            make_trade(pnl=100, timestamp=BASE_TS + timedelta(hours=i))
            for i in range(3)
        ] + [
            make_trade(pnl=-50, timestamp=BASE_TS + timedelta(hours=3 + i))
            for i in range(2)
        ] + [
            make_trade(pnl=80, timestamp=BASE_TS + timedelta(hours=5)),
        ]

        result = engine.streak_analysis(trades)

        assert result["max_win_streak"] == 3
        assert result["max_loss_streak"] == 2
        assert result["current_streak"]["type"] == "win"
        assert result["current_streak"]["count"] == 1


# =====================================================================
# equity_curve
# =====================================================================
class TestEquityCurve:

    def test_equity_curve(self):
        trades = [
            make_trade(pnl=100, timestamp=BASE_TS),
            make_trade(pnl=-30, timestamp=BASE_TS + timedelta(hours=1)),
            make_trade(pnl=50, timestamp=BASE_TS + timedelta(hours=2)),
        ]
        result = engine.equity_curve_data(trades)

        cum = result["cumulative_pnl"]
        assert len(cum) == 1  # all same day
        assert cum[0]["cumulative_pnl"] == 120.0  # 100 - 30 + 50
        assert cum[0]["trade_count"] == 3

    def test_equity_curve_multi_day(self):
        trades = [
            make_trade(pnl=100, timestamp=BASE_TS),
            make_trade(pnl=-30, timestamp=BASE_TS + timedelta(days=1)),
            make_trade(pnl=50, timestamp=BASE_TS + timedelta(days=2)),
        ]
        result = engine.equity_curve_data(trades)

        cum = result["cumulative_pnl"]
        assert len(cum) == 3
        assert cum[0]["cumulative_pnl"] == 100.0
        assert cum[1]["cumulative_pnl"] == 70.0   # 100 - 30
        assert cum[2]["cumulative_pnl"] == 120.0   # 100 - 30 + 50


# =====================================================================
# risk_metrics
# =====================================================================
class TestRiskMetrics:

    def test_risk_metrics_sharpe(self):
        """30+ trading days with known daily PnL to verify Sharpe formula."""
        trades = []
        for i in range(35):
            ts = BASE_TS + timedelta(days=i)
            pnl = 50.0 if i % 2 == 0 else -20.0
            trades.append(make_trade(pnl=pnl, timestamp=ts))

        result = engine.risk_metrics(trades)

        assert "sharpe_ratio" in result
        assert result["sharpe_ratio"] is not None
        assert result["trading_days"] == 35

        # Manually compute expected Sharpe
        daily = [50.0 if i % 2 == 0 else -20.0 for i in range(35)]
        import statistics
        avg = statistics.mean(daily)
        std = statistics.stdev(daily)
        expected = round((avg / std) * math.sqrt(252), 2)
        assert result["sharpe_ratio"] == expected

    def test_risk_metrics_insufficient_data(self):
        trades = [
            make_trade(pnl=100, timestamp=BASE_TS + timedelta(hours=i))
            for i in range(5)
        ]
        result = engine.risk_metrics(trades)

        assert result["sharpe_ratio"] is None
        assert result["sortino_ratio"] is None
        assert result["var_95"] is None
        assert result["calmar_ratio"] is None


# =====================================================================
# timezone offset
# =====================================================================
class TestTimezoneOffset:

    def test_timezone_offset(self):
        """A trade at UTC 23:00 should show hour=4 with tz_offset=5."""
        trades = [
            make_trade(pnl=100, timestamp=datetime(2024, 6, 10, 23, 0, tzinfo=timezone.utc)),
            make_trade(pnl=-50, timestamp=datetime(2024, 6, 11, 1, 0, tzinfo=timezone.utc)),
        ]
        result = engine.time_analysis(trades, tz_offset_hours=5)

        assert 4 in result["trades_by_hour"]   # 23 + 5 = 28 -> next day hour 4
        assert 6 in result["trades_by_hour"]   # 1 + 5 = 6
        assert 23 not in result["trades_by_hour"]
