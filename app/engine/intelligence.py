"""
Intelligence Alerts Engine — generates personalized behavioral coaching messages.

Takes trades + rule violations and produces plain-language alerts like:
  "You lost ₹2,400 to revenge trading this month"
  "You break your rules after 2 consecutive losses"
  "Your FOMO trades have a 23% win rate vs 61% normally"

This is TradeLoop's moat — hedge funds don't give retail traders this.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from app.models.trade import Trade
from app.models.rule_violation import RuleViolation


class IntelligenceEngine:

    def generate_alerts(
        self,
        trades: List[Trade],
        violations: List[RuleViolation],
        tz_offset_hours: float = 0,
    ) -> Dict:
        if not trades:
            return {"alerts": [], "summary": None}

        alerts = []

        alerts.extend(self._mood_cost_alerts(trades))
        alerts.extend(self._mistake_pattern_alerts(trades))
        alerts.extend(self._post_loss_behavior_alerts(trades))
        alerts.extend(self._rule_violation_alerts(violations))
        alerts.extend(self._time_pattern_alerts(trades, tz_offset_hours))

        alerts.sort(key=lambda a: {"critical": 0, "warning": 1, "insight": 2}.get(a["severity"], 3))

        summary = self._build_summary(trades, alerts)

        return {
            "alerts": alerts[:15],
            "total_alerts": len(alerts),
            "summary": summary,
        }

    def _mood_cost_alerts(self, trades: List[Trade]) -> List[Dict]:
        """How much did each mood cost the trader?"""
        alerts = []
        mood_groups: Dict[str, List[Trade]] = defaultdict(list)
        for t in trades:
            if t.mood:
                mood_groups[t.mood].append(t)

        non_tagged = [t for t in trades if not t.mood]
        if non_tagged:
            base_wr = sum(1 for t in non_tagged if t.pnl > 0) / len(non_tagged) * 100 if non_tagged else 0
        else:
            base_wr = sum(1 for t in trades if t.pnl > 0) / len(trades) * 100

        bad_moods = {"revenge", "fomo", "anxious", "fearful", "greedy"}
        for mood, mood_trades in mood_groups.items():
            if mood not in bad_moods or len(mood_trades) < 2:
                continue

            total_pnl = sum(t.pnl for t in mood_trades)
            wr = sum(1 for t in mood_trades if t.pnl > 0) / len(mood_trades) * 100

            if total_pnl < 0:
                alerts.append({
                    "type": "mood_cost",
                    "severity": "critical" if total_pnl < -1000 else "warning",
                    "title": f"{mood.title()} trading is costing you money",
                    "message": (
                        f"You lost ₹{abs(round(total_pnl, 2))} across {len(mood_trades)} "
                        f"{mood} trades ({round(wr, 1)}% win rate vs {round(base_wr, 1)}% normally)"
                    ),
                    "action": self._mood_action(mood),
                    "impact": round(total_pnl, 2),
                })

        return alerts

    def _mistake_pattern_alerts(self, trades: List[Trade]) -> List[Dict]:
        """Detect recurring mistake categories."""
        alerts = []
        mistake_groups: Dict[str, List[Trade]] = defaultdict(list)
        for t in trades:
            if t.mistake_category and t.mistake_category != "none":
                mistake_groups[t.mistake_category].append(t)

        total_trades = len(trades)
        for mistake, mistake_trades in mistake_groups.items():
            if len(mistake_trades) < 3:
                continue

            pct = len(mistake_trades) / total_trades * 100
            total_pnl = sum(t.pnl for t in mistake_trades)

            alerts.append({
                "type": "recurring_mistake",
                "severity": "warning",
                "title": f"Recurring mistake: {mistake.replace('_', ' ').title()}",
                "message": (
                    f"You made the '{mistake.replace('_', ' ')}' mistake {len(mistake_trades)} times "
                    f"({round(pct, 1)}% of trades), costing ₹{abs(round(total_pnl, 2))}"
                ),
                "action": self._mistake_action(mistake),
                "impact": round(total_pnl, 2),
            })

        return alerts

    def _post_loss_behavior_alerts(self, trades: List[Trade]) -> List[Dict]:
        """What happens after consecutive losses? Do they break rules?"""
        alerts = []
        if len(trades) < 10:
            return alerts

        broke_rules_after_losses = 0
        followed_rules_after_losses = 0
        consec_loss_threshold = 2

        consec = 0
        for i, t in enumerate(trades):
            if t.pnl < 0:
                consec += 1
            else:
                consec = 0

            if consec >= consec_loss_threshold and i + 1 < len(trades):
                next_trade = trades[i + 1]
                if next_trade.rule_followed is False:
                    broke_rules_after_losses += 1
                elif next_trade.rule_followed is True:
                    followed_rules_after_losses += 1

        total_after = broke_rules_after_losses + followed_rules_after_losses
        if total_after >= 3 and broke_rules_after_losses > followed_rules_after_losses:
            pct = round(broke_rules_after_losses / total_after * 100, 1)
            alerts.append({
                "type": "behavioral_pattern",
                "severity": "critical",
                "title": "You break rules after consecutive losses",
                "message": (
                    f"After {consec_loss_threshold}+ losses in a row, you broke your rules "
                    f"{broke_rules_after_losses} out of {total_after} times ({pct}%)"
                ),
                "action": "Set a hard stop: after 2 consecutive losses, take a 30-minute break. No exceptions.",
                "impact": None,
            })

        return alerts

    def _rule_violation_alerts(self, violations: List[RuleViolation]) -> List[Dict]:
        """Summarize rule violations into actionable alerts."""
        if not violations:
            return []

        alerts = []
        by_type: Dict[str, List[RuleViolation]] = defaultdict(list)
        for v in violations:
            by_type[v.rule_type].append(v)

        for rule_type, type_violations in by_type.items():
            critical_count = sum(1 for v in type_violations if v.severity == "critical")
            alerts.append({
                "type": "rule_violation_summary",
                "severity": "critical" if critical_count > 0 else "warning",
                "title": f"Rule violated: {rule_type.replace('_', ' ').title()}",
                "message": (
                    f"Your '{rule_type.replace('_', ' ')}' rule was violated "
                    f"{len(type_violations)} times"
                ),
                "action": f"Review your {rule_type.replace('_', ' ')} rule and consider tightening it",
                "impact": None,
            })

        return alerts

    def _time_pattern_alerts(self, trades: List[Trade], tz_offset_hours: float) -> List[Dict]:
        """Detect time-of-day patterns worth alerting on."""
        alerts = []
        if len(trades) < 20:
            return alerts

        offset = timedelta(hours=tz_offset_hours)
        morning: List[Trade] = []
        afternoon: List[Trade] = []

        for t in trades:
            local_hour = (t.timestamp + offset).hour
            if local_hour < 12:
                morning.append(t)
            else:
                afternoon.append(t)

        if len(morning) >= 10 and len(afternoon) >= 10:
            am_wr = sum(1 for t in morning if t.pnl > 0) / len(morning) * 100
            pm_wr = sum(1 for t in afternoon if t.pnl > 0) / len(afternoon) * 100
            am_pnl = sum(t.pnl for t in morning)
            pm_pnl = sum(t.pnl for t in afternoon)

            if abs(am_wr - pm_wr) > 15:
                better = "morning" if am_wr > pm_wr else "afternoon"
                worse = "afternoon" if better == "morning" else "morning"
                worse_pnl = pm_pnl if worse == "afternoon" else am_pnl
                alerts.append({
                    "type": "time_pattern",
                    "severity": "insight",
                    "title": f"You trade better in the {better}",
                    "message": (
                        f"Morning win rate: {round(am_wr, 1)}% (P&L: ₹{round(am_pnl, 2)}), "
                        f"Afternoon: {round(pm_wr, 1)}% (P&L: ₹{round(pm_pnl, 2)})"
                    ),
                    "action": f"Consider reducing {worse} trading or using smaller positions",
                    "impact": round(worse_pnl, 2) if worse_pnl < 0 else None,
                })

        return alerts

    def _build_summary(self, trades: List[Trade], alerts: List[Dict]) -> Optional[Dict]:
        """One-paragraph behavioral summary."""
        if not alerts:
            return None

        critical = [a for a in alerts if a["severity"] == "critical"]
        total_impact = sum(a.get("impact", 0) or 0 for a in alerts if (a.get("impact") or 0) < 0)

        rule_violations_count = sum(1 for t in trades if t.rule_followed is False)
        total_tagged = sum(1 for t in trades if t.rule_followed is not None)
        compliance_rate = round(
            (total_tagged - rule_violations_count) / total_tagged * 100, 1
        ) if total_tagged > 0 else None

        return {
            "critical_issues": len(critical),
            "total_behavioral_cost": round(abs(total_impact), 2) if total_impact < 0 else 0,
            "compliance_rate": compliance_rate,
            "top_issue": critical[0]["title"] if critical else (alerts[0]["title"] if alerts else None),
            "message": self._summary_message(trades, critical, total_impact, compliance_rate),
        }

    def _summary_message(
        self, trades: List[Trade], critical: List, total_impact: float, compliance_rate: Optional[float]
    ) -> str:
        parts = []
        if total_impact < 0:
            parts.append(f"Behavioral mistakes cost you ₹{abs(round(total_impact, 2))}")
        if compliance_rate is not None:
            parts.append(f"Rule compliance: {compliance_rate}%")
        if critical:
            parts.append(f"{len(critical)} critical issue(s) need attention")
        if not parts:
            parts.append("No major behavioral issues detected. Keep it up!")
        return ". ".join(parts) + "."

    def _mood_action(self, mood: str) -> str:
        actions = {
            "revenge": "After a loss, set a 10-minute timer. Do not place any trade until it rings.",
            "fomo": "If you didn't plan a trade before the market opened, don't take it.",
            "anxious": "Reduce position size by 50% after 2 consecutive losses.",
            "fearful": "Review your stop-loss levels. Fear often means your risk is too large.",
            "greedy": "Take profits at your pre-planned levels. Move stop to breakeven after 1R.",
        }
        return actions.get(mood, "Review your trading journal for this pattern.")

    def _mistake_action(self, mistake: str) -> str:
        actions = {
            "early_exit": "Set your stop-loss and take-profit before entering. Don't touch them.",
            "late_exit": "Use trailing stops or time-based exits to lock in profits.",
            "no_stop_loss": "Never enter a trade without a stop-loss. Make it a hard rule.",
            "moved_stop_loss": "Once set, your stop-loss is sacred. Moving it = breaking a rule.",
            "oversized": "Cap position size at 2% of account per trade. No exceptions.",
            "undersized": "If your conviction is low, skip the trade entirely rather than sizing down.",
            "fomo_entry": "Only trade setups from your playbook. If it's not in the playbook, it's not a trade.",
            "revenge": "After a loss, close your platform for 10 minutes. Come back with fresh eyes.",
            "chased": "If you missed the entry, the trade is gone. Wait for the next setup.",
            "ignored_signal": "Trust your system. If the signal says go, go. If it says stop, stop.",
            "overtraded": "Set a daily trade limit and stick to it. Quality over quantity.",
        }
        return actions.get(mistake, "Review this pattern in your trade journal.")


intelligence_engine = IntelligenceEngine()
