"""
Counterfactual Analysis Engine — TradeLoop's differentiator.

Not "you revenge traded 12 times" but "revenge trading cost you exactly ₹47,230.
Here is your equity curve with and without those trades."

Every insight has: pattern name, dollar impact, confidence, what-if curve, recommendation.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from dataclasses import dataclass
from datetime import timedelta
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class Insight:
    """A single counterfactual insight with dollar-value impact."""
    id: str
    title: str
    category: str  # "revenge", "timing", "sizing", "overtrading", "tilt", "session"
    severity: str  # "critical", "major", "minor", "positive"
    dollar_impact: float  # negative = money lost, positive = money gained
    monthly_projection: float  # projected monthly savings if fixed
    description: str
    recommendation: str
    confidence: float  # 0-1, based on sample size
    actual_equity: List[dict]  # [{date, pnl}] actual cumulative
    counterfactual_equity: List[dict]  # [{date, pnl}] without this pattern
    affected_trade_count: int
    affected_trade_indices: List[int]
    stats: dict


class CounterfactualEngine:
    """Compute what-if scenarios for every behavioral leak."""

    def analyze(self, trades: list, tz_offset_hours: float = 0) -> dict:
        """Run all counterfactual analyses and return insights ranked by dollar impact."""
        if len(trades) < 10:
            return {"insights": [], "summary": {"total_leaks": 0, "total_dollar_impact": 0}}

        sorted_trades = sorted(trades, key=lambda t: t.timestamp)
        offset = timedelta(hours=tz_offset_hours)

        insights: List[Optional[Insight]] = []
        insights.append(self._revenge_trade_cost(sorted_trades))
        insights.append(self._overtrading_cost(sorted_trades, offset))
        insights.append(self._tilt_cost(sorted_trades))
        insights.append(self._bad_hours_cost(sorted_trades, offset))
        insights.append(self._bad_days_cost(sorted_trades, offset))
        insights.append(self._first_last_trade_cost(sorted_trades, offset))
        insights.append(self._sizing_leak_cost(sorted_trades))
        insights.append(self._optimal_session_detection(sorted_trades, offset))

        valid = [i for i in insights if i is not None]
        valid.sort(key=lambda i: abs(i.dollar_impact), reverse=True)

        leaks = [i for i in valid if i.dollar_impact < 0]
        edges = [i for i in valid if i.dollar_impact > 0]

        actual_equity = self._build_equity_curve(sorted_trades, set())

        if len(sorted_trades) >= 2:
            days = (sorted_trades[-1].timestamp - sorted_trades[0].timestamp).days
            months = max(days / 30.0, 1)
        else:
            months = 1

        return {
            "insights": [self._insight_to_dict(i) for i in valid],
            "summary": {
                "total_leaks_found": len(leaks),
                "total_edges_found": len(edges),
                "total_money_leaked": round(sum(i.dollar_impact for i in leaks), 2),
                "total_edge_value": round(sum(i.dollar_impact for i in edges), 2),
                "projected_monthly_savings": round(abs(sum(i.dollar_impact for i in leaks)) / months, 2),
                "actual_total_pnl": round(sum(t.pnl for t in sorted_trades), 2),
                "potential_total_pnl": round(
                    sum(t.pnl for t in sorted_trades) - sum(i.dollar_impact for i in leaks), 2
                ),
            },
            "actual_equity": actual_equity,
        }

    def _revenge_trade_cost(self, trades: list) -> Optional[Insight]:
        """What if you never revenge traded?"""
        revenge_indices: Set[int] = set()
        for i in range(1, len(trades)):
            if trades[i - 1].pnl < 0:
                gap = (trades[i].timestamp - trades[i - 1].timestamp).total_seconds()
                if 0 < gap <= 300:
                    revenge_indices.add(i)

        if len(revenge_indices) < 2:
            return None

        total_pnl = sum(trades[i].pnl for i in revenge_indices)
        revenge_wr = sum(1 for i in revenge_indices if trades[i].pnl > 0) / len(revenge_indices) * 100
        normal_indices = set(range(len(trades))) - revenge_indices
        normal_wr = (
            sum(1 for i in normal_indices if trades[i].pnl > 0) / len(normal_indices) * 100
            if normal_indices
            else 0
        )

        counterfactual = self._build_equity_curve(trades, revenge_indices)
        actual = self._build_equity_curve(trades, set())

        days = max((trades[-1].timestamp - trades[0].timestamp).days / 30, 1)

        return Insight(
            id="revenge_trades",
            title="Revenge Trading Cost",
            category="revenge",
            severity="critical" if total_pnl < -500 else "major" if total_pnl < 0 else "minor",
            dollar_impact=round(total_pnl, 2),
            monthly_projection=round(abs(total_pnl) / days, 2) if total_pnl < 0 else 0,
            description=(
                f"You took {len(revenge_indices)} revenge trades (within 5 min of a loss). "
                f"Win rate: {round(revenge_wr, 1)}% vs {round(normal_wr, 1)}% normally. "
                f"Net impact: ₹{round(total_pnl, 2)}."
            ),
            recommendation=(
                "Set a mandatory 10-minute cooldown after any losing trade. "
                "Walk away from the screen. Your win rate drops dramatically when you chase losses."
            ),
            confidence=min(1.0, len(revenge_indices) / 10),
            actual_equity=actual,
            counterfactual_equity=counterfactual,
            affected_trade_count=len(revenge_indices),
            affected_trade_indices=sorted(revenge_indices),
            stats={
                "revenge_win_rate": round(revenge_wr, 2),
                "normal_win_rate": round(normal_wr, 2),
                "avg_revenge_pnl": round(total_pnl / len(revenge_indices), 2),
            },
        )

    def _overtrading_cost(self, trades: list, offset: timedelta) -> Optional[Insight]:
        """What if you stopped at your average daily trade count?"""
        daily: Dict[str, list] = defaultdict(list)
        for i, t in enumerate(trades):
            day = (t.timestamp + offset).date().isoformat()
            daily[day].append((i, t))

        if len(daily) < 5:
            return None

        avg_count = statistics.mean(len(v) for v in daily.values())
        threshold = int(avg_count * 2)
        if threshold < 4:
            return None

        excess_indices: Set[int] = set()
        for day, day_trades in daily.items():
            if len(day_trades) > threshold:
                sorted_day = sorted(day_trades, key=lambda x: x[1].timestamp)
                for idx, (i, t) in enumerate(sorted_day):
                    if idx >= threshold:
                        excess_indices.add(i)

        if len(excess_indices) < 3:
            return None

        excess_pnl = sum(trades[i].pnl for i in excess_indices)
        counterfactual = self._build_equity_curve(trades, excess_indices)
        actual = self._build_equity_curve(trades, set())

        days = max((trades[-1].timestamp - trades[0].timestamp).days / 30, 1)

        return Insight(
            id="overtrading",
            title="Overtrading Cost",
            category="overtrading",
            severity="critical" if excess_pnl < -500 else "major" if excess_pnl < 0 else "minor",
            dollar_impact=round(excess_pnl, 2),
            monthly_projection=round(abs(excess_pnl) / days, 2) if excess_pnl < 0 else 0,
            description=(
                f"On high-volume days (>{threshold} trades), the excess trades "
                f"({len(excess_indices)} total) had a net P&L of ₹{round(excess_pnl, 2)}."
            ),
            recommendation=(
                f"Cap yourself at {threshold} trades per day. Your excess trades are "
                f"{'losing money' if excess_pnl < 0 else 'marginally profitable but add risk'}."
            ),
            confidence=min(1.0, len(excess_indices) / 15),
            actual_equity=actual,
            counterfactual_equity=counterfactual,
            affected_trade_count=len(excess_indices),
            affected_trade_indices=sorted(excess_indices),
            stats={"threshold": threshold, "avg_daily": round(avg_count, 1)},
        )

    def _tilt_cost(self, trades: list) -> Optional[Insight]:
        """Cost of sizing up after consecutive losses."""
        tilt_indices: Set[int] = set()
        consec_losses = 0
        for i in range(1, len(trades)):
            if trades[i - 1].pnl < 0:
                consec_losses += 1
            else:
                consec_losses = 0
            if consec_losses >= 2 and trades[i].quantity > trades[i - 1].quantity * 1.2:
                tilt_indices.add(i)

        if len(tilt_indices) < 2:
            return None

        tilt_pnl = sum(trades[i].pnl for i in tilt_indices)
        counterfactual = self._build_equity_curve(trades, tilt_indices)
        actual = self._build_equity_curve(trades, set())
        days = max((trades[-1].timestamp - trades[0].timestamp).days / 30, 1)

        return Insight(
            id="tilt_sizing",
            title="Tilt Sizing Cost",
            category="tilt",
            severity="critical" if tilt_pnl < -500 else "major" if tilt_pnl < 0 else "minor",
            dollar_impact=round(tilt_pnl, 2),
            monthly_projection=round(abs(tilt_pnl) / days, 2) if tilt_pnl < 0 else 0,
            description=(
                f"You increased position size {len(tilt_indices)} times after consecutive losses. "
                f"Net result: ₹{round(tilt_pnl, 2)}."
            ),
            recommendation=(
                "Never increase size after losses. Keep position size constant or reduce it. "
                "Sizing up on tilt is the fastest way to blow an account."
            ),
            confidence=min(1.0, len(tilt_indices) / 8),
            actual_equity=actual,
            counterfactual_equity=counterfactual,
            affected_trade_count=len(tilt_indices),
            affected_trade_indices=sorted(tilt_indices),
            stats={},
        )

    def _bad_hours_cost(self, trades: list, offset: timedelta) -> Optional[Insight]:
        """What if you only traded during your profitable hours?"""
        hour_pnl: Dict[int, list] = defaultdict(list)
        hour_indices: Dict[int, list] = defaultdict(list)
        for i, t in enumerate(trades):
            h = (t.timestamp + offset).hour
            hour_pnl[h].append(t.pnl)
            hour_indices[h].append(i)

        bad_hours = []
        for h, pnls in hour_pnl.items():
            if len(pnls) >= 5 and sum(pnls) < 0:
                bad_hours.append(h)

        if not bad_hours:
            return None

        bad_indices: Set[int] = set()
        for h in bad_hours:
            bad_indices.update(hour_indices[h])

        bad_pnl = sum(trades[i].pnl for i in bad_indices)
        counterfactual = self._build_equity_curve(trades, bad_indices)
        actual = self._build_equity_curve(trades, set())
        days = max((trades[-1].timestamp - trades[0].timestamp).days / 30, 1)

        hour_strs = [f"{h}:00" for h in sorted(bad_hours)]
        good_hours = sorted(set(hour_pnl.keys()) - set(bad_hours))
        good_strs = [f"{h}:00" for h in good_hours] if good_hours else ["none identified"]

        return Insight(
            id="bad_hours",
            title="Unprofitable Hours",
            category="timing",
            severity="critical" if bad_pnl < -1000 else "major" if bad_pnl < -200 else "minor",
            dollar_impact=round(bad_pnl, 2),
            monthly_projection=round(abs(bad_pnl) / days, 2) if bad_pnl < 0 else 0,
            description=(
                f"Trading during {', '.join(hour_strs)} cost you ₹{abs(round(bad_pnl, 2))}. "
                f"Your profitable hours: {', '.join(good_strs)}."
            ),
            recommendation=(
                f"Restrict trading to {', '.join(good_strs)}. "
                f"Close your charts during {', '.join(hour_strs)}."
            ),
            confidence=min(1.0, len(bad_indices) / 20),
            actual_equity=actual,
            counterfactual_equity=counterfactual,
            affected_trade_count=len(bad_indices),
            affected_trade_indices=sorted(bad_indices),
            stats={"bad_hours": sorted(bad_hours), "good_hours": good_hours},
        )

    def _bad_days_cost(self, trades: list, offset: timedelta) -> Optional[Insight]:
        """What if you skipped your worst day of the week?"""
        dow_pnl: Dict[int, float] = defaultdict(float)
        dow_indices: Dict[int, list] = defaultdict(list)
        dow_count: Dict[int, int] = defaultdict(int)
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        for i, t in enumerate(trades):
            d = (t.timestamp + offset).weekday()
            dow_pnl[d] += t.pnl
            dow_indices[d].append(i)
            dow_count[d] += 1

        worst_day = min(dow_pnl, key=dow_pnl.get)  # type: ignore[arg-type]
        if dow_pnl[worst_day] >= 0 or dow_count[worst_day] < 5:
            return None

        bad_indices = set(dow_indices[worst_day])
        bad_pnl = dow_pnl[worst_day]
        counterfactual = self._build_equity_curve(trades, bad_indices)
        actual = self._build_equity_curve(trades, set())
        days = max((trades[-1].timestamp - trades[0].timestamp).days / 30, 1)

        return Insight(
            id="bad_day_of_week",
            title=f"{day_names[worst_day]} Losses",
            category="timing",
            severity="major" if bad_pnl < -500 else "minor",
            dollar_impact=round(bad_pnl, 2),
            monthly_projection=round(abs(bad_pnl) / days, 2),
            description=(
                f"{day_names[worst_day]}s cost you ₹{abs(round(bad_pnl, 2))} across "
                f"{dow_count[worst_day]} trades."
            ),
            recommendation=(
                f"Consider reducing size or skipping {day_names[worst_day]}s entirely. "
                f"Your edge is concentrated on other days."
            ),
            confidence=min(1.0, dow_count[worst_day] / 15),
            actual_equity=actual,
            counterfactual_equity=counterfactual,
            affected_trade_count=len(bad_indices),
            affected_trade_indices=sorted(bad_indices),
            stats={
                "day": day_names[worst_day],
                "pnl_per_day": {day_names[d]: round(p, 2) for d, p in dow_pnl.items()},
            },
        )

    def _first_last_trade_cost(self, trades: list, offset: timedelta) -> Optional[Insight]:
        """Cost of the last trade of day (often emotional/revenge)."""
        daily: Dict[str, list] = defaultdict(list)
        for i, t in enumerate(trades):
            day = (t.timestamp + offset).date().isoformat()
            daily[day].append((i, t))

        last_indices: Set[int] = set()
        for day, day_trades in daily.items():
            if len(day_trades) >= 3:
                sorted_day = sorted(day_trades, key=lambda x: x[1].timestamp)
                last_indices.add(sorted_day[-1][0])

        if len(last_indices) < 5:
            return None

        last_pnl = sum(trades[i].pnl for i in last_indices)
        last_wr = sum(1 for i in last_indices if trades[i].pnl > 0) / len(last_indices) * 100
        other_wr = (
            sum(1 for i in range(len(trades)) if i not in last_indices and trades[i].pnl > 0)
            / max(1, len(trades) - len(last_indices))
            * 100
        )

        if last_wr >= other_wr - 5:
            return None

        counterfactual = self._build_equity_curve(trades, last_indices)
        actual = self._build_equity_curve(trades, set())
        days = max((trades[-1].timestamp - trades[0].timestamp).days / 30, 1)

        return Insight(
            id="last_trade_of_day",
            title="Last Trade of Day Cost",
            category="timing",
            severity="major" if last_pnl < -300 else "minor",
            dollar_impact=round(last_pnl, 2),
            monthly_projection=round(abs(last_pnl) / days, 2) if last_pnl < 0 else 0,
            description=(
                f"Your last trade of the day has a {round(last_wr, 1)}% win rate vs "
                f"{round(other_wr, 1)}% for others. Cost: ₹{abs(round(last_pnl, 2))}."
            ),
            recommendation=(
                "Stop trading 30 minutes before your planned end time. "
                "The last trade is often emotional — you're trying to 'end green'."
            ),
            confidence=min(1.0, len(last_indices) / 10),
            actual_equity=actual,
            counterfactual_equity=counterfactual,
            affected_trade_count=len(last_indices),
            affected_trade_indices=sorted(last_indices),
            stats={"last_trade_wr": round(last_wr, 2), "other_wr": round(other_wr, 2)},
        )

    def _sizing_leak_cost(self, trades: list) -> Optional[Insight]:
        """Cost of changing position size after losses vs maintaining consistency."""
        if len(trades) < 20:
            return None

        quantities = [t.quantity for t in trades]
        avg_qty = statistics.mean(quantities)
        std_qty = statistics.stdev(quantities) if len(quantities) > 1 else 0

        if std_qty < avg_qty * 0.1:
            return Insight(
                id="consistent_sizing",
                title="Consistent Position Sizing",
                category="sizing",
                severity="positive",
                dollar_impact=0,
                monthly_projection=0,
                description="Your position sizing is consistent. This is a sign of disciplined trading.",
                recommendation="Keep it up. Consistent sizing is one of the strongest edges.",
                confidence=0.9,
                actual_equity=self._build_equity_curve(trades, set()),
                counterfactual_equity=[],
                affected_trade_count=0,
                affected_trade_indices=[],
                stats={"avg_size": round(avg_qty, 2), "size_std": round(std_qty, 2)},
            )

        oversized_indices: Set[int] = set()
        for i, t in enumerate(trades):
            if t.quantity > avg_qty * 1.5 and t.pnl < 0:
                oversized_indices.add(i)

        if len(oversized_indices) < 3:
            return None

        oversized_pnl = sum(trades[i].pnl for i in oversized_indices)
        counterfactual = self._build_equity_curve(trades, oversized_indices)
        actual = self._build_equity_curve(trades, set())
        days = max((trades[-1].timestamp - trades[0].timestamp).days / 30, 1)

        return Insight(
            id="oversized_losers",
            title="Oversized Losing Trades",
            category="sizing",
            severity="critical" if oversized_pnl < -1000 else "major",
            dollar_impact=round(oversized_pnl, 2),
            monthly_projection=round(abs(oversized_pnl) / days, 2),
            description=(
                f"{len(oversized_indices)} trades were >1.5x your average size AND lost money. "
                f"Total damage: ₹{abs(round(oversized_pnl, 2))}."
            ),
            recommendation=(
                f"Cap position size at {round(avg_qty * 1.2, 1)}. "
                f"Your biggest losses come from your biggest positions."
            ),
            confidence=min(1.0, len(oversized_indices) / 8),
            actual_equity=actual,
            counterfactual_equity=counterfactual,
            affected_trade_count=len(oversized_indices),
            affected_trade_indices=sorted(oversized_indices),
            stats={"avg_size": round(avg_qty, 2)},
        )

    def _optimal_session_detection(self, trades: list, offset: timedelta) -> Optional[Insight]:
        """Find the exact hours where your edge exists."""
        hour_data: Dict[int, dict] = defaultdict(lambda: {"pnl": 0.0, "count": 0, "wins": 0})
        for t in trades:
            h = (t.timestamp + offset).hour
            hour_data[h]["pnl"] += t.pnl
            hour_data[h]["count"] += 1
            if t.pnl > 0:
                hour_data[h]["wins"] += 1

        profitable_hours = [h for h, d in hour_data.items() if d["pnl"] > 0 and d["count"] >= 5]
        if not profitable_hours:
            return None

        edge_pnl = sum(hour_data[h]["pnl"] for h in profitable_hours)
        total_pnl = sum(d["pnl"] for d in hour_data.values())
        edge_concentration = (edge_pnl / total_pnl * 100) if total_pnl > 0 else 0

        if edge_concentration < 80:
            return None

        sorted_hours = sorted(profitable_hours)
        session_str = f"{sorted_hours[0]}:00-{sorted_hours[-1] + 1}:00"

        return Insight(
            id="optimal_session",
            title="Your Trading Edge Window",
            category="session",
            severity="positive",
            dollar_impact=round(edge_pnl, 2),
            monthly_projection=0,
            description=(
                f"Your edge is concentrated in {session_str}. "
                f"These hours account for {round(edge_concentration, 0)}% of your total profits."
            ),
            recommendation=(
                f"Focus exclusively on {session_str}. "
                f"Your profits come from this window — everything else is noise."
            ),
            confidence=min(1.0, sum(hour_data[h]["count"] for h in profitable_hours) / 30),
            actual_equity=self._build_equity_curve(trades, set()),
            counterfactual_equity=[],
            affected_trade_count=sum(hour_data[h]["count"] for h in profitable_hours),
            affected_trade_indices=[],
            stats={
                "profitable_hours": sorted_hours,
                "edge_concentration": round(edge_concentration, 1),
            },
        )

    # ===== HELPERS =====

    def _build_equity_curve(self, trades: list, exclude_indices: Set[int]) -> List[dict]:
        """Build cumulative P&L curve, optionally excluding specific trades."""
        running = 0.0
        daily: Dict[str, float] = {}
        for i, t in enumerate(trades):
            if i not in exclude_indices:
                running += t.pnl
            day = t.timestamp.date().isoformat()
            daily[day] = round(running, 2)
        return [{"date": d, "pnl": p} for d, p in daily.items()]

    def _insight_to_dict(self, insight: Insight) -> dict:
        # Merge actual and counterfactual into a single array for frontend charting
        actual = {p["date"]: p["pnl"] for p in insight.actual_equity}
        counter = {p["date"]: p["pnl"] for p in insight.counterfactual_equity}
        all_dates = sorted(set(list(actual.keys()) + list(counter.keys())))
        equity_curve = [
            {"date": d, "actual": actual.get(d, 0), "counterfactual": counter.get(d, 0)}
            for d in all_dates
        ][-30:]

        return {
            "id": insight.id,
            "title": insight.title,
            "category": insight.category,
            "severity": insight.severity,
            "dollar_impact": insight.dollar_impact,
            "monthly_projection": insight.monthly_projection,
            "description": insight.description,
            "recommendation": insight.recommendation,
            "confidence": round(insight.confidence, 2),
            "equity_curve": equity_curve,
            "affected_trade_count": insight.affected_trade_count,
            "stats": insight.stats,
        }
