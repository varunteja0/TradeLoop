"""
Weekly Intelligence Report Engine.

Generates a weekly performance summary with insights, grades, and comparisons.
"""
from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from app.engine.analytics import TradeAnalytics
from app.engine.counterfactual import CounterfactualEngine


class WeeklyReportEngine:
    def __init__(self):
        self.analytics = TradeAnalytics()
        self.insights_engine = CounterfactualEngine()

    def generate(self, all_trades: list, tz_offset_hours: int = 0,
                 week_end_date: Optional[datetime] = None) -> dict:
        if not all_trades:
            return {"has_data": False}

        sorted_trades = sorted(all_trades, key=lambda t: t.timestamp)
        now = week_end_date or (datetime.now(timezone.utc) + timedelta(hours=tz_offset_hours))
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        # Strip timezone for comparison since SQLite timestamps are naive
        now_naive = now.replace(tzinfo=None)
        week_start = now_naive - timedelta(days=7)
        prev_week_start = now_naive - timedelta(days=14)

        def ts_naive(t: object) -> datetime:
            ts = t.timestamp  # type: ignore
            return ts.replace(tzinfo=None) if ts.tzinfo else ts

        this_week = [t for t in sorted_trades if ts_naive(t) >= week_start]
        prev_week = [t for t in sorted_trades if prev_week_start <= ts_naive(t) < week_start]

        if not this_week:
            return {"has_data": False, "message": "No trades this week"}

        tw_metrics = self._week_metrics(this_week)
        pw_metrics = self._week_metrics(prev_week) if prev_week else None

        insights = self.insights_engine.analyze(sorted_trades, tz_offset_hours)
        top_insights = insights.get("insights", [])[:3]

        grade, grade_reasons = self._compute_grade(this_week, sorted_trades)

        focus = self._pick_focus(top_insights, tw_metrics)

        return {
            "has_data": True,
            "period": {
                "start": week_start.date().isoformat(),
                "end": now.date().isoformat(),
            },
            "this_week": tw_metrics,
            "previous_week": pw_metrics,
            "comparison": self._compare(tw_metrics, pw_metrics) if pw_metrics else None,
            "grade": grade,
            "grade_reasons": grade_reasons,
            "top_insights": top_insights,
            "focus_for_next_week": focus,
            "summary": self._build_summary(tw_metrics, grade, focus),
        }

    def _week_metrics(self, trades: list) -> dict:
        total = len(trades)
        winners = [t for t in trades if t.pnl > 0]
        losers = [t for t in trades if t.pnl < 0]
        total_pnl = sum(t.pnl for t in trades)

        revenge_count = 0
        for i in range(1, len(trades)):
            if trades[i-1].pnl < 0:
                gap = (trades[i].timestamp - trades[i-1].timestamp).total_seconds()
                if 0 < gap <= 300:
                    revenge_count += 1

        unique_days = len(set(t.timestamp.date() for t in trades))

        return {
            "total_trades": total,
            "winners": len(winners),
            "losers": len(losers),
            "win_rate": round(len(winners) / total * 100, 2) if total else 0,
            "total_pnl": round(total_pnl, 2),
            "avg_pnl": round(total_pnl / total, 2) if total else 0,
            "largest_winner": round(max((t.pnl for t in winners), default=0), 2),
            "largest_loser": round(min((t.pnl for t in losers), default=0), 2),
            "revenge_trades": revenge_count,
            "trading_days": unique_days,
            "avg_trades_per_day": round(total / max(unique_days, 1), 1),
        }

    def _compute_grade(self, this_week: list, all_trades: list) -> tuple:
        """Grade A-F based on discipline metrics."""
        score = 100
        reasons = []

        tw = self._week_metrics(this_week)

        if tw["revenge_trades"] > 0:
            penalty = min(30, tw["revenge_trades"] * 10)
            score -= penalty
            reasons.append(f"-{penalty} pts: {tw['revenge_trades']} revenge trades")

        if len(all_trades) >= 20:
            hist_wr = sum(1 for t in all_trades if t.pnl > 0) / len(all_trades) * 100
            if tw["win_rate"] > hist_wr + 5:
                score += 10
                reasons.append("+10 pts: Win rate above your average")
            elif tw["win_rate"] < hist_wr - 10:
                score -= 15
                reasons.append("-15 pts: Win rate below your average")

        if tw["total_pnl"] > 0:
            score += 10
            reasons.append("+10 pts: Profitable week")
        else:
            score -= 10
            reasons.append("-10 pts: Losing week")

        if tw["avg_trades_per_day"] <= 6:
            score += 5
            reasons.append("+5 pts: Disciplined trade frequency")

        score = max(0, min(100, score))

        if score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 65:
            grade = "C"
        elif score >= 50:
            grade = "D"
        else:
            grade = "F"

        return grade, reasons

    def _compare(self, this_week: dict, prev_week: dict) -> dict:
        return {
            "pnl_change": round(this_week["total_pnl"] - prev_week["total_pnl"], 2),
            "win_rate_change": round(this_week["win_rate"] - prev_week["win_rate"], 2),
            "trade_count_change": this_week["total_trades"] - prev_week["total_trades"],
            "revenge_change": this_week["revenge_trades"] - prev_week["revenge_trades"],
            "improved": this_week["total_pnl"] > prev_week["total_pnl"],
        }

    def _pick_focus(self, insights: list, tw_metrics: dict) -> dict:
        if insights and insights[0].get("dollar_impact", 0) < -100:
            top = insights[0]
            return {
                "area": top["title"],
                "why": top["description"],
                "action": top["recommendation"],
                "potential_savings": abs(top["dollar_impact"]),
            }
        if tw_metrics["revenge_trades"] > 0:
            return {
                "area": "Revenge Trading",
                "why": f"You revenge traded {tw_metrics['revenge_trades']} times this week.",
                "action": "Set a 10-minute timer after every loss before placing another trade.",
                "potential_savings": None,
            }
        return {
            "area": "Consistency",
            "why": "Keep doing what you're doing.",
            "action": "Focus on executing your best setups with consistent sizing.",
            "potential_savings": None,
        }

    def _build_summary(self, tw: dict, grade: str, focus: dict) -> str:
        pnl_word = "profit" if tw["total_pnl"] >= 0 else "loss"
        return (
            f"This week: {tw['total_trades']} trades, "
            f"₹{abs(tw['total_pnl'])} {pnl_word}, "
            f"{tw['win_rate']}% win rate. "
            f"Grade: {grade}. "
            f"Focus for next week: {focus['area']}."
        )
