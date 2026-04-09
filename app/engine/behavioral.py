"""
Behavioral Pattern Detection — TradeLoop's killer feature.

Detects the behavioral leaks that cost traders money:
revenge trading, tilt, overtrading, streak effects, sizing errors.
Every pattern is specific and actionable.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import timedelta

from app.models.trade import Trade


class BehavioralAnalyzer:

    def analyze(self, trades: list[Trade], tz_offset_hours: float = 0) -> dict:
        if len(trades) < 5:
            return {"insufficient_data": True, "min_trades_needed": 5}

        return {
            "revenge_trades": self._revenge_trades(trades),
            "overtrading_days": self._overtrading_days(trades, tz_offset_hours),
            "tilt_detection": self._tilt_detection(trades),
            "win_streak_behavior": self._streak_behavior(trades, streak_type="win"),
            "loss_streak_behavior": self._streak_behavior(trades, streak_type="loss"),
            "monday_effect": self._day_effect(trades, target_day=0, label="Monday", tz_offset_hours=tz_offset_hours),
            "friday_effect": self._day_effect(trades, target_day=4, label="Friday", tz_offset_hours=tz_offset_hours),
            "first_trade_of_day": self._position_in_day(trades, position="first", tz_offset_hours=tz_offset_hours),
            "last_trade_of_day": self._position_in_day(trades, position="last", tz_offset_hours=tz_offset_hours),
            "sizing_after_loss": self._sizing_after_outcome(trades),
            "time_between_trades": self._time_between_trades(trades),
        }

    def _revenge_trades(self, trades: list[Trade]) -> dict:
        """Trades taken within 5 minutes of a losing trade."""
        revenge = []
        revenge_indices: set[int] = set()
        for i in range(1, len(trades)):
            prev = trades[i - 1]
            curr = trades[i]
            if prev.pnl < 0:
                gap = (curr.timestamp - prev.timestamp).total_seconds()
                if 0 < gap <= 300:
                    revenge.append(curr)
                    revenge_indices.add(i)

        if not revenge:
            return {"count": 0, "win_rate": None, "avg_pnl": None, "total_pnl": None,
                    "alert": None}

        wins = sum(1 for t in revenge if t.pnl > 0)
        total_pnl = sum(t.pnl for t in revenge)

        non_revenge_trades = [t for i, t in enumerate(trades) if i not in revenge_indices]
        non_revenge_wr = (
            sum(1 for t in non_revenge_trades if t.pnl > 0) / len(non_revenge_trades) * 100
            if non_revenge_trades else 0
        )

        wr = round(wins / len(revenge) * 100, 2)
        return {
            "count": len(revenge),
            "win_rate": wr,
            "avg_pnl": round(total_pnl / len(revenge), 2),
            "total_pnl": round(total_pnl, 2),
            "percentage_of_trades": round(len(revenge) / len(trades) * 100, 1),
            "normal_win_rate": round(non_revenge_wr, 2),
            "alert": (
                f"You revenge traded {len(revenge)} times ({round(len(revenge)/len(trades)*100, 1)}% of trades). "
                f"Win rate on revenge trades: {wr}% vs {round(non_revenge_wr, 2)}% normally. "
                f"Total P&L from revenge trades: ₹{round(total_pnl, 2)}."
            ) if len(revenge) >= 3 else None,
        }

    def _overtrading_days(self, trades: list[Trade], tz_offset_hours: float = 0) -> dict:
        """Days with more than 2x the average daily trade count."""
        offset = timedelta(hours=tz_offset_hours)
        daily_counts: dict[str, list[Trade]] = defaultdict(list)
        for t in trades:
            day_key = (t.timestamp + offset).date().isoformat()
            daily_counts[day_key].append(t)

        if not daily_counts:
            return {"days": [], "avg_daily_trades": 0}

        avg_daily = statistics.mean(len(v) for v in daily_counts.values())
        threshold = avg_daily * 2

        overtrading = []
        for date, day_trades in daily_counts.items():
            if len(day_trades) > threshold:
                pnl = sum(t.pnl for t in day_trades)
                overtrading.append({
                    "date": date,
                    "trade_count": len(day_trades),
                    "pnl": round(pnl, 2),
                })

        total_pnl_overtrading = sum(d["pnl"] for d in overtrading)

        return {
            "count": len(overtrading),
            "avg_daily_trades": round(avg_daily, 1),
            "threshold": round(threshold, 1),
            "days": sorted(overtrading, key=lambda x: x["pnl"])[:10],
            "total_pnl_on_overtrading_days": round(total_pnl_overtrading, 2),
            "alert": (
                f"You overtraded on {len(overtrading)} days (>{round(threshold, 0):.0f} trades/day). "
                f"Total P&L on those days: ₹{round(total_pnl_overtrading, 2)}."
            ) if overtrading else None,
        }

    def _tilt_detection(self, trades: list[Trade]) -> dict:
        """Did position size increase after consecutive losses?"""
        tilt_events = []
        consec_losses = 0

        for i in range(1, len(trades)):
            if trades[i - 1].pnl < 0:
                consec_losses += 1
            else:
                consec_losses = 0

            if consec_losses >= 2:
                prev_qty = trades[i - 1].quantity
                curr_qty = trades[i].quantity
                if curr_qty > prev_qty * 1.2:
                    tilt_events.append({
                        "trade_index": i,
                        "timestamp": trades[i].timestamp.isoformat(),
                        "consecutive_losses_before": consec_losses,
                        "size_increase_pct": round((curr_qty / prev_qty - 1) * 100, 1),
                        "outcome_pnl": round(trades[i].pnl, 2),
                    })

        outcomes = [e["outcome_pnl"] for e in tilt_events]
        return {
            "tilt_events": len(tilt_events),
            "events": tilt_events[:10],
            "avg_outcome": round(statistics.mean(outcomes), 2) if outcomes else None,
            "total_pnl_from_tilt": round(sum(outcomes), 2) if outcomes else 0,
            "alert": (
                f"Detected {len(tilt_events)} tilt events where you sized up after consecutive losses. "
                f"Average outcome: ₹{round(statistics.mean(outcomes), 2)}."
            ) if len(tilt_events) >= 2 else None,
        }

    def _streak_behavior(self, trades: list[Trade], streak_type: str, min_streak: int = 3) -> dict:
        """What happens after N+ consecutive wins or losses?"""
        next_trades_after_streak: list[Trade] = []
        consec = 0
        target_positive = streak_type == "win"

        for i in range(len(trades)):
            is_match = (trades[i].pnl > 0) if target_positive else (trades[i].pnl < 0)
            if is_match:
                consec += 1
            else:
                if consec >= min_streak:
                    next_trades_after_streak.append(trades[i])
                consec = 0

        if not next_trades_after_streak:
            return {
                "streak_threshold": min_streak,
                "occurrences": 0,
                "next_trade_win_rate": None,
                "next_trade_avg_pnl": None,
            }

        wins_after = sum(1 for t in next_trades_after_streak if t.pnl > 0)
        return {
            "streak_threshold": min_streak,
            "occurrences": len(next_trades_after_streak),
            "next_trade_win_rate": round(wins_after / len(next_trades_after_streak) * 100, 2),
            "next_trade_avg_pnl": round(
                sum(t.pnl for t in next_trades_after_streak) / len(next_trades_after_streak), 2
            ),
        }

    def _day_effect(
        self,
        trades: list[Trade],
        target_day: int,
        label: str,
        tz_offset_hours: float = 0,
    ) -> dict:
        """Is a specific day significantly different from other days?"""
        offset = timedelta(hours=tz_offset_hours)
        target = [t for t in trades if (t.timestamp + offset).weekday() == target_day]
        others = [t for t in trades if (t.timestamp + offset).weekday() != target_day]

        if not target or not others:
            return {"has_data": False}

        target_wr = sum(1 for t in target if t.pnl > 0) / len(target) * 100
        other_wr = sum(1 for t in others if t.pnl > 0) / len(others) * 100
        target_pnl = sum(t.pnl for t in target)

        diff = target_wr - other_wr
        significant = abs(diff) > 10 and len(target) >= 5

        return {
            "has_data": True,
            "day": label,
            "trades": len(target),
            "win_rate": round(target_wr, 2),
            "other_days_win_rate": round(other_wr, 2),
            "difference": round(diff, 2),
            "total_pnl": round(target_pnl, 2),
            "is_significant": significant,
            "alert": (
                f"{label}s are {'worse' if diff < 0 else 'better'} than other days: "
                f"{round(target_wr, 1)}% win rate vs {round(other_wr, 1)}%. "
                f"Total {label} P&L: ₹{round(target_pnl, 2)}."
            ) if significant else None,
        }

    def _position_in_day(
        self,
        trades: list[Trade],
        position: str,
        tz_offset_hours: float = 0,
    ) -> dict:
        """Win rate of first or last trade of the day vs the rest."""
        offset = timedelta(hours=tz_offset_hours)
        daily: dict[str, list[Trade]] = defaultdict(list)
        for t in trades:
            day_key = (t.timestamp + offset).date().isoformat()
            daily[day_key].append(t)

        target_trades: list[Trade] = []
        rest_trades: list[Trade] = []
        multi_trade_days = 0

        for date, day_trades in daily.items():
            sorted_day = sorted(day_trades, key=lambda t: t.timestamp)
            if len(sorted_day) < 2:
                continue

            multi_trade_days += 1
            if position == "first":
                target_trades.append(sorted_day[0])
                rest_trades.extend(sorted_day[1:])
            else:
                target_trades.append(sorted_day[-1])
                rest_trades.extend(sorted_day[:-1])

        if not target_trades or multi_trade_days < 5:
            return {"has_data": False}

        target_wr = sum(1 for t in target_trades if t.pnl > 0) / len(target_trades) * 100
        rest_wr = sum(1 for t in rest_trades if t.pnl > 0) / len(rest_trades) * 100 if rest_trades else 0
        target_avg_pnl = sum(t.pnl for t in target_trades) / len(target_trades)

        return {
            "has_data": True,
            "position": position,
            "trades": len(target_trades),
            "win_rate": round(target_wr, 2),
            "rest_win_rate": round(rest_wr, 2),
            "avg_pnl": round(target_avg_pnl, 2),
            "difference": round(target_wr - rest_wr, 2),
            "alert": (
                f"Your {position} trade of the day has a {round(target_wr, 1)}% win rate "
                f"vs {round(rest_wr, 1)}% for other trades. Avg P&L: ₹{round(target_avg_pnl, 2)}."
            ) if abs(target_wr - rest_wr) > 10 else None,
        }

    def _sizing_after_outcome(self, trades: list[Trade]) -> dict:
        """Average position size after a win vs after a loss."""
        size_after_win = []
        size_after_loss = []

        for i in range(1, len(trades)):
            if trades[i - 1].pnl > 0:
                size_after_win.append(trades[i].quantity)
            elif trades[i - 1].pnl < 0:
                size_after_loss.append(trades[i].quantity)

        if not size_after_win or not size_after_loss:
            return {"has_data": False}

        avg_after_win = statistics.mean(size_after_win)
        avg_after_loss = statistics.mean(size_after_loss)
        ratio = avg_after_loss / avg_after_win if avg_after_win > 0 else 1

        return {
            "has_data": True,
            "avg_size_after_win": round(avg_after_win, 2),
            "avg_size_after_loss": round(avg_after_loss, 2),
            "ratio": round(ratio, 2),
            "alert": (
                f"You size {'up' if ratio > 1.15 else 'down'} after losses: "
                f"avg size {round(avg_after_loss, 1)} after loss vs {round(avg_after_win, 1)} after win."
            ) if abs(ratio - 1) > 0.15 else None,
        }

    def _time_between_trades(self, trades: list[Trade]) -> dict:
        """Does shorter time between trades correlate with worse performance?"""
        if len(trades) < 10:
            return {"has_data": False}

        gaps = []
        for i in range(1, len(trades)):
            gap_seconds = (trades[i].timestamp - trades[i - 1].timestamp).total_seconds()
            if gap_seconds > 0:
                gaps.append((gap_seconds / 60, trades[i].pnl))

        if not gaps:
            return {"has_data": False}

        avg_gap = statistics.mean(g[0] for g in gaps)
        fast_trades = [(g, pnl) for g, pnl in gaps if g < avg_gap]
        slow_trades = [(g, pnl) for g, pnl in gaps if g >= avg_gap]

        fast_wr = (
            sum(1 for _, pnl in fast_trades if pnl > 0) / len(fast_trades) * 100
            if fast_trades else 0
        )
        slow_wr = (
            sum(1 for _, pnl in slow_trades if pnl > 0) / len(slow_trades) * 100
            if slow_trades else 0
        )
        fast_avg_pnl = statistics.mean(pnl for _, pnl in fast_trades) if fast_trades else 0
        slow_avg_pnl = statistics.mean(pnl for _, pnl in slow_trades) if slow_trades else 0

        return {
            "has_data": True,
            "avg_gap_minutes": round(avg_gap, 1),
            "fast_trades_count": len(fast_trades),
            "fast_trades_win_rate": round(fast_wr, 2),
            "fast_trades_avg_pnl": round(fast_avg_pnl, 2),
            "slow_trades_count": len(slow_trades),
            "slow_trades_win_rate": round(slow_wr, 2),
            "slow_trades_avg_pnl": round(slow_avg_pnl, 2),
            "alert": (
                f"Quick trades (< {round(avg_gap, 0):.0f} min gap) have a {round(fast_wr, 1)}% win rate "
                f"vs {round(slow_wr, 1)}% for patient trades. "
                f"Avg P&L: ₹{round(fast_avg_pnl, 2)} vs ₹{round(slow_avg_pnl, 2)}."
            ) if abs(fast_wr - slow_wr) > 8 else None,
        }
