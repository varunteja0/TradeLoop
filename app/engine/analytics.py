"""
TradeLoop Analytics Engine — the core IP.

Deterministic trade analytics. Pure math on trade data.
No LLM. No external APIs. Every number must be correct.
"""

from __future__ import annotations

import math
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from app.models.trade import Trade


@dataclass
class FullAnalytics:
    overview: dict = field(default_factory=dict)
    time_analysis: dict = field(default_factory=dict)
    behavioral: dict = field(default_factory=dict)
    symbols: dict = field(default_factory=dict)
    streaks: dict = field(default_factory=dict)
    equity_curve: dict = field(default_factory=dict)
    risk_metrics: dict = field(default_factory=dict)


SESSIONS = {
    "asian": (0, 8),
    "london": (8, 13),
    "new_york": (13, 21),
    "after_hours": (21, 24),
}

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class TradeAnalytics:
    """Deterministic trade analytics engine. Pure math on trade data."""

    def compute_all(self, trades: list[Trade], tz_offset_hours: int = 0) -> FullAnalytics:
        if not trades:
            return FullAnalytics()

        sorted_trades = sorted(trades, key=lambda t: t.timestamp)
        return FullAnalytics(
            overview=self.overall_metrics(sorted_trades, tz_offset_hours=tz_offset_hours),
            time_analysis=self.time_analysis(sorted_trades, tz_offset_hours=tz_offset_hours),
            behavioral=self.behavioral_analysis(sorted_trades),
            symbols=self.symbol_analysis(sorted_trades),
            streaks=self.streak_analysis(sorted_trades),
            equity_curve=self.equity_curve_data(sorted_trades, tz_offset_hours=tz_offset_hours),
            risk_metrics=self.risk_metrics(sorted_trades, tz_offset_hours=tz_offset_hours),
        )

    # =====================================================================
    # HELPERS
    # =====================================================================
    @staticmethod
    def _adjust_ts(ts: datetime, tz_offset_hours: int) -> datetime:
        if tz_offset_hours == 0:
            return ts
        return ts + timedelta(hours=tz_offset_hours)

    @staticmethod
    def _get_session(hour: int) -> str:
        for name, (start, end) in SESSIONS.items():
            if start <= hour < end:
                return name
        return "after_hours"

    # =====================================================================
    # PERFORMANCE METRICS
    # =====================================================================
    def overall_metrics(self, trades: list[Trade], tz_offset_hours: int = 0) -> dict:
        total = len(trades)
        if total == 0:
            return {}

        winners = [t for t in trades if t.pnl > 0]
        losers = [t for t in trades if t.pnl < 0]
        scratches = [t for t in trades if t.pnl == 0]

        gross_profit = sum(t.pnl for t in winners)
        gross_loss = abs(sum(t.pnl for t in losers))

        win_rate = len(winners) / total
        avg_winner = gross_profit / len(winners) if winners else 0
        avg_loser = gross_loss / len(losers) if losers else 0
        loss_rate = len(losers) / total

        hold_times = [t.duration_minutes for t in trades if t.duration_minutes is not None]
        total_fees = sum(t.fees for t in trades)

        daily_pnl = defaultdict(float)
        for t in trades:
            adj = self._adjust_ts(t.timestamp, tz_offset_hours)
            daily_pnl[adj.date().isoformat()] += t.pnl

        best_day = max(daily_pnl.items(), key=lambda x: x[1]) if daily_pnl else (None, 0)
        worst_day = min(daily_pnl.items(), key=lambda x: x[1]) if daily_pnl else (None, 0)

        return {
            "total_trades": total,
            "winners": len(winners),
            "losers": len(losers),
            "scratches": len(scratches),
            "win_rate": round(win_rate * 100, 2),
            "gross_profit": round(gross_profit, 2),
            "gross_loss": round(gross_loss, 2),
            "average_winner": round(avg_winner, 2),
            "average_loser": round(avg_loser, 2),
            "largest_winner": round(max(t.pnl for t in winners), 2) if winners else 0,
            "largest_loser": round(min(t.pnl for t in losers), 2) if losers else 0,
            "profit_factor": round(gross_profit / gross_loss, 2) if gross_loss > 0 else None,
            "expectancy": round(avg_winner * win_rate - avg_loser * loss_rate, 2),
            "total_pnl": round(sum(t.pnl for t in trades), 2),
            "total_fees": round(total_fees, 2),
            "net_pnl": round(sum(t.pnl for t in trades) - total_fees, 2),
            "average_hold_time_minutes": round(statistics.mean(hold_times), 1) if hold_times else None,
            "best_day": {"date": best_day[0], "pnl": round(best_day[1], 2)},
            "worst_day": {"date": worst_day[0], "pnl": round(worst_day[1], 2)},
        }

    # =====================================================================
    # TIME ANALYSIS
    # =====================================================================
    def time_analysis(self, trades: list[Trade], tz_offset_hours: int = 0) -> dict:
        if not trades:
            return {}

        hour_wins = defaultdict(int)
        hour_total = defaultdict(int)
        hour_pnl = defaultdict(float)

        dow_wins = defaultdict(int)
        dow_total = defaultdict(int)
        dow_pnl = defaultdict(float)

        session_wins = defaultdict(int)
        session_total = defaultdict(int)
        session_pnl = defaultdict(float)

        for t in trades:
            adj = self._adjust_ts(t.timestamp, tz_offset_hours)
            h = adj.hour
            hour_total[h] += 1
            hour_pnl[h] += t.pnl
            if t.pnl > 0:
                hour_wins[h] += 1

            dow = DAY_NAMES[adj.weekday()]
            dow_total[dow] += 1
            dow_pnl[dow] += t.pnl
            if t.pnl > 0:
                dow_wins[dow] += 1

            session = self._get_session(h)
            session_total[session] += 1
            session_pnl[session] += t.pnl
            if t.pnl > 0:
                session_wins[session] += 1

        win_rate_by_hour = {
            h: round(hour_wins[h] / hour_total[h] * 100, 2)
            for h in sorted(hour_total)
        }
        pnl_by_hour = {h: round(hour_pnl[h], 2) for h in sorted(hour_pnl)}

        win_rate_by_dow = {
            d: round(dow_wins[d] / dow_total[d] * 100, 2)
            for d in DAY_NAMES if d in dow_total
        }
        pnl_by_dow = {d: round(dow_pnl[d], 2) for d in DAY_NAMES if d in dow_pnl}

        win_rate_by_session = {
            s: round(session_wins[s] / session_total[s] * 100, 2)
            for s in session_total
        }
        pnl_by_session = {s: round(session_pnl[s], 2) for s in session_pnl}

        best_hour = max(pnl_by_hour, key=pnl_by_hour.get) if pnl_by_hour else None
        worst_hour = min(pnl_by_hour, key=pnl_by_hour.get) if pnl_by_hour else None
        best_dow = max(pnl_by_dow, key=pnl_by_dow.get) if pnl_by_dow else None
        worst_dow = min(pnl_by_dow, key=pnl_by_dow.get) if pnl_by_dow else None

        return {
            "win_rate_by_hour": win_rate_by_hour,
            "pnl_by_hour": pnl_by_hour,
            "trades_by_hour": dict(sorted(hour_total.items())),
            "win_rate_by_day_of_week": win_rate_by_dow,
            "pnl_by_day_of_week": pnl_by_dow,
            "trades_by_day_of_week": {d: dow_total[d] for d in DAY_NAMES if d in dow_total},
            "best_hour": best_hour,
            "worst_hour": worst_hour,
            "best_day": best_dow,
            "worst_day": worst_dow,
            "win_rate_by_session": win_rate_by_session,
            "pnl_by_session": pnl_by_session,
            "trades_by_session": dict(session_total),
        }

    # =====================================================================
    # SYMBOL / INSTRUMENT ANALYSIS
    # =====================================================================
    def symbol_analysis(self, trades: list[Trade]) -> dict:
        if not trades:
            return {}

        sym_data: dict[str, dict] = defaultdict(lambda: {
            "trades": 0, "wins": 0, "total_pnl": 0.0, "pnls": [],
            "hold_times": [],
        })

        for t in trades:
            s = sym_data[t.symbol]
            s["trades"] += 1
            s["total_pnl"] += t.pnl
            s["pnls"].append(t.pnl)
            if t.pnl > 0:
                s["wins"] += 1
            if t.duration_minutes is not None:
                s["hold_times"].append(t.duration_minutes)

        per_symbol = {}
        for sym, d in sym_data.items():
            per_symbol[sym] = {
                "trades": d["trades"],
                "win_rate": round(d["wins"] / d["trades"] * 100, 2),
                "total_pnl": round(d["total_pnl"], 2),
                "avg_pnl": round(d["total_pnl"] / d["trades"], 2),
                "avg_hold_time": round(statistics.mean(d["hold_times"]), 1) if d["hold_times"] else None,
            }

        sorted_by_pnl = sorted(per_symbol.items(), key=lambda x: x[1]["total_pnl"], reverse=True)
        best = [{"symbol": s, **d} for s, d in sorted_by_pnl[:3]]
        worst = [{"symbol": s, **d} for s, d in sorted_by_pnl[-3:]]

        top3_trades = sum(per_symbol[s]["trades"] for s, _ in sorted_by_pnl[:3])
        concentration = round(top3_trades / len(trades) * 100, 2) if trades else 0

        return {
            "per_symbol": per_symbol,
            "best_symbols": best,
            "worst_symbols": worst,
            "concentration_top3": concentration,
        }

    # =====================================================================
    # STREAK ANALYSIS
    # =====================================================================
    def streak_analysis(self, trades: list[Trade]) -> dict:
        if not trades:
            return {}

        streaks: list[dict] = []
        current_type = "win" if trades[0].pnl > 0 else "loss"
        current_count = 1
        current_pnl = trades[0].pnl
        start_date = trades[0].timestamp.isoformat()

        for t in trades[1:]:
            t_type = "win" if t.pnl > 0 else "loss"
            if t.pnl == 0:
                t_type = current_type

            if t_type == current_type:
                current_count += 1
                current_pnl += t.pnl
            else:
                streaks.append({
                    "type": current_type,
                    "count": current_count,
                    "pnl": round(current_pnl, 2),
                    "start_date": start_date,
                    "end_date": t.timestamp.isoformat(),
                })
                current_type = t_type
                current_count = 1
                current_pnl = t.pnl
                start_date = t.timestamp.isoformat()

        streaks.append({
            "type": current_type,
            "count": current_count,
            "pnl": round(current_pnl, 2),
            "start_date": start_date,
            "end_date": trades[-1].timestamp.isoformat(),
        })

        win_streaks = [s for s in streaks if s["type"] == "win"]
        loss_streaks = [s for s in streaks if s["type"] == "loss"]

        return {
            "current_streak": {"type": streaks[-1]["type"], "count": streaks[-1]["count"]},
            "max_win_streak": max((s["count"] for s in win_streaks), default=0),
            "max_loss_streak": max((s["count"] for s in loss_streaks), default=0),
            "avg_win_streak": round(statistics.mean(s["count"] for s in win_streaks), 1) if win_streaks else 0,
            "avg_loss_streak": round(statistics.mean(s["count"] for s in loss_streaks), 1) if loss_streaks else 0,
            "streaks_history": streaks[-20:],
        }

    # =====================================================================
    # EQUITY CURVE
    # =====================================================================
    def equity_curve_data(self, trades: list[Trade], tz_offset_hours: int = 0) -> dict:
        if not trades:
            return {}

        running = 0.0
        daily_agg: dict[str, dict] = {}

        for t in trades:
            running += t.pnl
            adj = self._adjust_ts(t.timestamp, tz_offset_hours)
            date_str = adj.date().isoformat()
            if date_str not in daily_agg:
                daily_agg[date_str] = {"cumulative_pnl": 0.0, "trade_count": 0}
            daily_agg[date_str]["cumulative_pnl"] = round(running, 2)
            daily_agg[date_str]["trade_count"] += 1

        cumulative = [
            {"date": d, "cumulative_pnl": v["cumulative_pnl"], "trade_count": v["trade_count"]}
            for d, v in daily_agg.items()
        ]

        # Drawdown
        peak = 0.0
        min_during_dd = 0.0
        drawdown_periods = []
        current_dd_start = None

        for point in cumulative:
            pnl = point["cumulative_pnl"]
            if pnl > peak:
                if current_dd_start is not None and peak > 0:
                    drawdown_periods.append({
                        "start": current_dd_start,
                        "end": point["date"],
                        "depth": round(peak - min_during_dd, 2),
                    })
                peak = pnl
                current_dd_start = None
            elif pnl < peak:
                if current_dd_start is None:
                    current_dd_start = point["date"]
                    min_during_dd = pnl
                else:
                    min_during_dd = min(min_during_dd, pnl)

        max_dd = {"amount": 0, "start": None, "end": None}
        if drawdown_periods:
            worst = max(drawdown_periods, key=lambda d: d["depth"])
            max_dd = worst

        # Rolling 20-trade metrics
        rolling_wr_20 = []
        rolling_pnl_20 = []
        for i in range(len(trades)):
            window = trades[max(0, i - 19):i + 1]
            wr = sum(1 for t in window if t.pnl > 0) / len(window)
            rpnl = sum(t.pnl for t in window)
            rolling_wr_20.append(round(wr * 100, 2))
            rolling_pnl_20.append(round(rpnl, 2))

        return {
            "cumulative_pnl": cumulative,
            "drawdown_periods": drawdown_periods[:10],
            "max_drawdown": max_dd,
            "rolling_win_rate_20": rolling_wr_20[-50:],
            "rolling_pnl_20": rolling_pnl_20[-50:],
        }

    # =====================================================================
    # RISK METRICS
    # =====================================================================
    def risk_metrics(self, trades: list[Trade], tz_offset_hours: int = 0) -> dict:
        if not trades:
            return {}

        daily_pnl: dict[str, float] = defaultdict(float)
        for t in trades:
            adj = self._adjust_ts(t.timestamp, tz_offset_hours)
            daily_pnl[adj.date().isoformat()] += t.pnl

        daily_returns = list(daily_pnl.values())
        winners = [t for t in trades if t.pnl > 0]
        losers = [t for t in trades if t.pnl < 0]

        avg_winner = statistics.mean(t.pnl for t in winners) if winners else 0
        avg_loser = abs(statistics.mean(t.pnl for t in losers)) if losers else 0
        avg_rr = round(avg_winner / avg_loser, 2) if avg_loser > 0 else None

        max_consec_loss = 0
        current_consec = 0
        for t in trades:
            if t.pnl < 0:
                current_consec += 1
                max_consec_loss = max(max_consec_loss, current_consec)
            else:
                current_consec = 0

        avg_daily = statistics.mean(daily_returns) if daily_returns else 0
        std_daily = statistics.stdev(daily_returns) if len(daily_returns) > 1 else 0

        result: dict = {
            "average_risk_reward": avg_rr,
            "max_consecutive_losses": max_consec_loss,
            "average_daily_pnl": round(avg_daily, 2),
            "std_daily_pnl": round(std_daily, 2),
            "trading_days": len(daily_returns),
        }

        if len(daily_returns) >= 30:
            if std_daily > 0:
                result["sharpe_ratio"] = round((avg_daily / std_daily) * math.sqrt(252), 2)
            else:
                result["sharpe_ratio"] = None

            # Sortino — downside deviation of ALL returns (0 for non-negative)
            downside_returns = [min(0, r) for r in daily_returns]
            downside_dev = (sum(r ** 2 for r in downside_returns) / len(downside_returns)) ** 0.5
            if downside_dev > 0:
                result["sortino_ratio"] = round((avg_daily / downside_dev) * math.sqrt(252), 2)
            else:
                result["sortino_ratio"] = None

            if std_daily > 0:
                result["var_95"] = round(avg_daily - 1.645 * std_daily, 2)
            else:
                result["var_95"] = None

            # Calmar — trade-by-trade running equity for accurate max drawdown
            running = 0.0
            eq_peak = 0.0
            max_dd_val = 0.0
            for t in trades:
                running += t.pnl
                eq_peak = max(eq_peak, running)
                max_dd_val = max(max_dd_val, eq_peak - running)
            total_return = sum(daily_returns)
            years = len(daily_returns) / 252
            annual_return = total_return / years if years > 0 else 0
            result["calmar_ratio"] = round(annual_return / max_dd_val, 2) if max_dd_val > 0 else None
        else:
            result["sharpe_ratio"] = None
            result["sortino_ratio"] = None
            result["var_95"] = None
            result["calmar_ratio"] = None

        return result

    # =====================================================================
    # EMOTION / MOOD ANALYSIS
    # =====================================================================
    def emotion_analysis(self, trades: list) -> dict:
        """Correlate emotional tags with performance."""
        tagged = [t for t in trades if getattr(t, 'mood', None)]
        if len(tagged) < 5:
            return {"has_data": False, "message": "Tag at least 5 trades with emotions to see correlations"}

        mood_stats: dict = {}
        for t in tagged:
            mood = t.mood
            if mood not in mood_stats:
                mood_stats[mood] = {"trades": 0, "wins": 0, "total_pnl": 0.0, "pnls": []}
            mood_stats[mood]["trades"] += 1
            mood_stats[mood]["total_pnl"] += t.pnl
            mood_stats[mood]["pnls"].append(t.pnl)
            if t.pnl > 0:
                mood_stats[mood]["wins"] += 1

        result = {}
        for mood, stats in mood_stats.items():
            result[mood] = {
                "trades": stats["trades"],
                "win_rate": round(stats["wins"] / stats["trades"] * 100, 2),
                "total_pnl": round(stats["total_pnl"], 2),
                "avg_pnl": round(stats["total_pnl"] / stats["trades"], 2),
            }

        best_mood = max(result.items(), key=lambda x: x[1]["avg_pnl"])
        worst_mood = min(result.items(), key=lambda x: x[1]["avg_pnl"])

        return {
            "has_data": True,
            "per_mood": result,
            "best_mood": {"mood": best_mood[0], **best_mood[1]},
            "worst_mood": {"mood": worst_mood[0], **worst_mood[1]},
            "total_tagged": len(tagged),
            "total_trades": len(trades),
            "tag_rate": round(len(tagged) / len(trades) * 100, 1) if trades else 0,
            "insight": (
                f"You perform best when '{best_mood[0]}' (avg ₹{best_mood[1]['avg_pnl']}/trade) "
                f"and worst when '{worst_mood[0]}' (avg ₹{worst_mood[1]['avg_pnl']}/trade)."
            ) if len(result) >= 2 else "Tag more trades to see patterns.",
        }

    # =====================================================================
    # BEHAVIORAL ANALYSIS (delegated to behavioral.py)
    # =====================================================================
    def behavioral_analysis(self, trades: list[Trade]) -> dict:
        from app.engine.behavioral import BehavioralAnalyzer
        return BehavioralAnalyzer().analyze(trades)
