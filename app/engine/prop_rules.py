"""
Prop Firm Compliance Engine — real-time rule monitoring.

Defines presets for major prop firms (FTMO, FundingPips, MyForexFunds, The5ers, TopStep)
and checks every trade against daily loss limits, max drawdown, profit targets,
consistency rules, and firm-specific restrictions.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


FIRM_PRESETS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "ftmo": {
        "challenge": {
            "daily_loss_limit_pct": 5.0,
            "max_drawdown_pct": 10.0,
            "drawdown_type": "static",
            "profit_target_pct": 10.0,
            "min_trading_days": 4,
            "consistency_rule_pct": None,
            "max_per_trade_risk_pct": None,
            "news_trading_allowed": True,
            "weekend_holding_allowed": True,
        },
        "funded": {
            "daily_loss_limit_pct": 5.0,
            "max_drawdown_pct": 10.0,
            "drawdown_type": "static",
            "profit_target_pct": None,
            "min_trading_days": 4,
            "consistency_rule_pct": None,
            "max_per_trade_risk_pct": None,
            "news_trading_allowed": True,
            "weekend_holding_allowed": True,
        },
    },
    "fundingpips": {
        "challenge": {
            "daily_loss_limit_pct": 5.0,
            "max_drawdown_pct": 10.0,
            "drawdown_type": "trailing",
            "profit_target_pct": 8.0,
            "min_trading_days": 5,
            "consistency_rule_pct": 30.0,
            "max_per_trade_risk_pct": 2.0,
            "news_trading_allowed": False,
            "weekend_holding_allowed": False,
        },
        "funded": {
            "daily_loss_limit_pct": 5.0,
            "max_drawdown_pct": 10.0,
            "drawdown_type": "trailing",
            "profit_target_pct": None,
            "min_trading_days": 5,
            "consistency_rule_pct": 30.0,
            "max_per_trade_risk_pct": 2.0,
            "news_trading_allowed": False,
            "weekend_holding_allowed": False,
        },
    },
    "myforexfunds": {
        "challenge": {
            "daily_loss_limit_pct": 5.0,
            "max_drawdown_pct": 8.0,
            "drawdown_type": "static",
            "profit_target_pct": 8.0,
            "min_trading_days": 5,
            "consistency_rule_pct": 35.0,
            "max_per_trade_risk_pct": 2.0,
            "news_trading_allowed": True,
            "weekend_holding_allowed": False,
        },
        "funded": {
            "daily_loss_limit_pct": 5.0,
            "max_drawdown_pct": 8.0,
            "drawdown_type": "static",
            "profit_target_pct": None,
            "min_trading_days": 5,
            "consistency_rule_pct": 35.0,
            "max_per_trade_risk_pct": 2.0,
            "news_trading_allowed": True,
            "weekend_holding_allowed": False,
        },
    },
    "the5ers": {
        "challenge": {
            "daily_loss_limit_pct": 5.0,
            "max_drawdown_pct": 10.0,
            "drawdown_type": "trailing",
            "profit_target_pct": 8.0,
            "min_trading_days": 4,
            "consistency_rule_pct": 30.0,
            "max_per_trade_risk_pct": 2.0,
            "news_trading_allowed": True,
            "weekend_holding_allowed": True,
        },
        "funded": {
            "daily_loss_limit_pct": 5.0,
            "max_drawdown_pct": 10.0,
            "drawdown_type": "trailing",
            "profit_target_pct": None,
            "min_trading_days": 4,
            "consistency_rule_pct": 30.0,
            "max_per_trade_risk_pct": 2.0,
            "news_trading_allowed": True,
            "weekend_holding_allowed": True,
        },
    },
    "topstep": {
        "challenge": {
            "daily_loss_limit_pct": 5.0,
            "max_drawdown_pct": 8.0,
            "drawdown_type": "trailing",
            "profit_target_pct": 10.0,
            "min_trading_days": 10,
            "consistency_rule_pct": 30.0,
            "max_per_trade_risk_pct": 3.0,
            "news_trading_allowed": True,
            "weekend_holding_allowed": False,
        },
        "funded": {
            "daily_loss_limit_pct": 5.0,
            "max_drawdown_pct": 8.0,
            "drawdown_type": "trailing",
            "profit_target_pct": None,
            "min_trading_days": 10,
            "consistency_rule_pct": 30.0,
            "max_per_trade_risk_pct": 3.0,
            "news_trading_allowed": True,
            "weekend_holding_allowed": False,
        },
    },
}


@dataclass
class RuleStatus:
    """Status of a single compliance rule."""
    rule_name: str
    limit: float
    current: float
    remaining: float
    usage_pct: float
    status: str  # "safe", "warning", "critical", "violated"
    message: str


@dataclass
class ComplianceReport:
    """Full compliance report for a prop firm account."""
    firm: str
    phase: str
    initial_balance: float
    current_balance: float
    daily_pnl: float
    daily_loss_remaining: float
    max_drawdown_used: float
    max_drawdown_remaining: float
    profit_target_progress: Optional[float]
    trading_days_count: int
    min_trading_days_met: bool
    consistency_check: Optional[Dict[str, Any]]
    violations: List[RuleStatus]
    warnings: List[RuleStatus]
    critical_warnings: List[RuleStatus]
    all_rules: List[RuleStatus]
    overall_status: str  # "safe", "warning", "critical", "violated"
    risk_score: int  # 0-100
    summary: str


class PropComplianceEngine:
    """Monitor prop firm rule compliance in real-time."""

    def check_compliance(self, trades: list, account_config: dict) -> ComplianceReport:
        """
        Check all compliance rules against the trade history.

        account_config keys:
            initial_balance: float
            firm: str (key in FIRM_PRESETS, or "custom")
            phase: str ("challenge" or "funded")
            custom_rules: dict (optional, overrides preset values)
            tz_offset_hours: float (optional, default 0)
        """
        initial_balance = account_config["initial_balance"]
        firm = account_config.get("firm", "custom")
        phase = account_config.get("phase", "challenge")
        tz_offset_hours = account_config.get("tz_offset_hours", 0)
        offset = timedelta(hours=tz_offset_hours)

        rules = self._resolve_rules(firm, phase, account_config.get("custom_rules"))
        sorted_trades = sorted(trades, key=lambda t: t.timestamp)

        current_balance = initial_balance + sum(t.pnl for t in sorted_trades)

        today_str = (datetime.utcnow() + offset).date().isoformat()
        daily_pnl = sum(
            t.pnl for t in sorted_trades
            if (t.timestamp + offset).date().isoformat() == today_str
        )

        peak_balance = initial_balance
        running_balance = initial_balance
        max_drawdown_from_peak = 0.0

        for t in sorted_trades:
            running_balance += t.pnl
            if rules["drawdown_type"] == "trailing":
                peak_balance = max(peak_balance, running_balance)
            drawdown = peak_balance - running_balance
            max_drawdown_from_peak = max(max_drawdown_from_peak, drawdown)

        daily_pnl_by_day: Dict[str, float] = defaultdict(float)
        for t in sorted_trades:
            day_key = (t.timestamp + offset).date().isoformat()
            daily_pnl_by_day[day_key] += t.pnl

        trading_days = len(daily_pnl_by_day)

        all_rules: List[RuleStatus] = []

        daily_loss_limit = initial_balance * rules["daily_loss_limit_pct"] / 100
        daily_loss_used = abs(min(daily_pnl, 0))
        daily_loss_remaining = max(daily_loss_limit - daily_loss_used, 0)
        daily_usage = (daily_loss_used / daily_loss_limit * 100) if daily_loss_limit > 0 else 0
        all_rules.append(RuleStatus(
            rule_name="Daily Loss Limit",
            limit=round(daily_loss_limit, 2),
            current=round(daily_loss_used, 2),
            remaining=round(daily_loss_remaining, 2),
            usage_pct=round(daily_usage, 1),
            status=self._status_from_usage(daily_usage),
            message=self._daily_loss_message(daily_usage, daily_loss_remaining),
        ))

        max_dd_limit = initial_balance * rules["max_drawdown_pct"] / 100
        dd_remaining = max(max_dd_limit - max_drawdown_from_peak, 0)
        dd_usage = (max_drawdown_from_peak / max_dd_limit * 100) if max_dd_limit > 0 else 0
        dd_type_label = "Trailing" if rules["drawdown_type"] == "trailing" else "Static"
        all_rules.append(RuleStatus(
            rule_name=f"Max Drawdown ({dd_type_label})",
            limit=round(max_dd_limit, 2),
            current=round(max_drawdown_from_peak, 2),
            remaining=round(dd_remaining, 2),
            usage_pct=round(dd_usage, 1),
            status=self._status_from_usage(dd_usage),
            message=self._drawdown_message(dd_usage, dd_remaining),
        ))

        profit_target_progress: Optional[float] = None
        if rules["profit_target_pct"] is not None:
            target_amount = initial_balance * rules["profit_target_pct"] / 100
            total_pnl = current_balance - initial_balance
            profit_target_progress = round(
                (total_pnl / target_amount * 100) if target_amount > 0 else 0, 1
            )
            all_rules.append(RuleStatus(
                rule_name="Profit Target",
                limit=round(target_amount, 2),
                current=round(max(total_pnl, 0), 2),
                remaining=round(max(target_amount - total_pnl, 0), 2),
                usage_pct=max(profit_target_progress, 0),
                status="safe",
                message=f"Progress: {max(profit_target_progress, 0):.1f}% of target reached.",
            ))

        min_days = rules["min_trading_days"]
        min_days_met = trading_days >= min_days
        all_rules.append(RuleStatus(
            rule_name="Minimum Trading Days",
            limit=float(min_days),
            current=float(trading_days),
            remaining=float(max(min_days - trading_days, 0)),
            usage_pct=round(trading_days / min_days * 100, 1) if min_days > 0 else 100,
            status="safe" if min_days_met else "warning",
            message=(
                f"Traded {trading_days}/{min_days} required days."
                if not min_days_met
                else f"Minimum trading days met ({trading_days}/{min_days})."
            ),
        ))

        consistency_check: Optional[Dict[str, Any]] = None
        if rules["consistency_rule_pct"] is not None:
            total_profit = sum(p for p in daily_pnl_by_day.values() if p > 0)
            consistency_limit = rules["consistency_rule_pct"]
            violating_days: List[Dict[str, Any]] = []
            if total_profit > 0:
                for day_key, pnl in daily_pnl_by_day.items():
                    if pnl > 0:
                        day_pct = pnl / total_profit * 100
                        if day_pct > consistency_limit:
                            violating_days.append({
                                "date": day_key,
                                "pnl": round(pnl, 2),
                                "pct_of_total": round(day_pct, 1),
                            })

            consistency_check = {
                "rule_pct": consistency_limit,
                "total_profit": round(total_profit, 2),
                "violating_days": violating_days,
                "is_consistent": len(violating_days) == 0,
            }

            worst_day_pct = (
                max((v["pct_of_total"] for v in violating_days), default=0)
            )
            con_usage = (worst_day_pct / consistency_limit * 100) if consistency_limit > 0 else 0
            all_rules.append(RuleStatus(
                rule_name="Consistency Rule",
                limit=consistency_limit,
                current=round(worst_day_pct, 1),
                remaining=round(max(consistency_limit - worst_day_pct, 0), 1),
                usage_pct=round(min(con_usage, 100), 1),
                status="violated" if violating_days else "safe",
                message=(
                    f"{len(violating_days)} day(s) exceed {consistency_limit}% of total profit."
                    if violating_days
                    else f"All days within {consistency_limit}% consistency rule."
                ),
            ))

        if rules["max_per_trade_risk_pct"] is not None:
            risk_limit = initial_balance * rules["max_per_trade_risk_pct"] / 100
            oversized_trades = [
                t for t in sorted_trades
                if abs(t.pnl) > risk_limit
            ]
            risk_usage = 0.0
            if oversized_trades:
                worst = max(abs(t.pnl) for t in oversized_trades)
                risk_usage = worst / risk_limit * 100

            all_rules.append(RuleStatus(
                rule_name="Per-Trade Risk Limit",
                limit=round(risk_limit, 2),
                current=round(max((abs(t.pnl) for t in sorted_trades), default=0), 2),
                remaining=round(
                    max(risk_limit - max((abs(t.pnl) for t in sorted_trades), default=0), 0), 2
                ),
                usage_pct=round(min(risk_usage, 100), 1),
                status=self._status_from_usage(min(risk_usage, 100)),
                message=(
                    f"{len(oversized_trades)} trade(s) exceeded per-trade risk limit."
                    if oversized_trades
                    else "All trades within per-trade risk limit."
                ),
            ))

        violations = [r for r in all_rules if r.status == "violated"]
        critical_warnings = [r for r in all_rules if r.status == "critical"]
        warnings = [r for r in all_rules if r.status == "warning"]

        if violations:
            overall_status = "violated"
        elif critical_warnings:
            overall_status = "critical"
        elif warnings:
            overall_status = "warning"
        else:
            overall_status = "safe"

        risk_score = self._compute_risk_score(all_rules)

        summary = self._build_summary(overall_status, violations, critical_warnings, warnings)

        return ComplianceReport(
            firm=firm,
            phase=phase,
            initial_balance=initial_balance,
            current_balance=round(current_balance, 2),
            daily_pnl=round(daily_pnl, 2),
            daily_loss_remaining=round(daily_loss_remaining, 2),
            max_drawdown_used=round(max_drawdown_from_peak, 2),
            max_drawdown_remaining=round(dd_remaining, 2),
            profit_target_progress=profit_target_progress,
            trading_days_count=trading_days,
            min_trading_days_met=min_days_met,
            consistency_check=consistency_check,
            violations=violations,
            warnings=warnings,
            critical_warnings=critical_warnings,
            all_rules=all_rules,
            overall_status=overall_status,
            risk_score=risk_score,
            summary=summary,
        )

    def _resolve_rules(
        self, firm: str, phase: str, custom_rules: Optional[dict]
    ) -> Dict[str, Any]:
        """Merge firm preset with any custom overrides."""
        firm_lower = firm.lower()
        if firm_lower in FIRM_PRESETS and phase in FIRM_PRESETS[firm_lower]:
            base = dict(FIRM_PRESETS[firm_lower][phase])
        else:
            base = {
                "daily_loss_limit_pct": 5.0,
                "max_drawdown_pct": 10.0,
                "drawdown_type": "static",
                "profit_target_pct": 10.0,
                "min_trading_days": 5,
                "consistency_rule_pct": None,
                "max_per_trade_risk_pct": None,
                "news_trading_allowed": True,
                "weekend_holding_allowed": True,
            }

        if custom_rules:
            base.update(custom_rules)

        return base

    @staticmethod
    def _status_from_usage(usage_pct: float) -> str:
        if usage_pct >= 100:
            return "violated"
        if usage_pct >= 90:
            return "critical"
        if usage_pct >= 70:
            return "warning"
        return "safe"

    @staticmethod
    def _daily_loss_message(usage_pct: float, remaining: float) -> str:
        if usage_pct >= 100:
            return "VIOLATED: Daily loss limit breached."
        if usage_pct >= 90:
            return f"CRITICAL: Only ₹{remaining:.2f} daily loss remaining."
        if usage_pct >= 70:
            return f"WARNING: ₹{remaining:.2f} daily loss remaining."
        return f"₹{remaining:.2f} daily loss remaining."

    @staticmethod
    def _drawdown_message(usage_pct: float, remaining: float) -> str:
        if usage_pct >= 100:
            return "VIOLATED: Maximum drawdown breached."
        if usage_pct >= 90:
            return f"CRITICAL: Only ₹{remaining:.2f} drawdown remaining."
        if usage_pct >= 70:
            return f"WARNING: ₹{remaining:.2f} drawdown remaining."
        return f"₹{remaining:.2f} drawdown buffer remaining."

    @staticmethod
    def _compute_risk_score(rules: List[RuleStatus]) -> int:
        """0 = perfectly safe, 100 = blown account."""
        if not rules:
            return 0

        max_usage = max(r.usage_pct for r in rules)
        avg_usage = sum(r.usage_pct for r in rules) / len(rules)

        score = int(max_usage * 0.6 + avg_usage * 0.4)
        return min(score, 100)

    @staticmethod
    def _build_summary(
        overall_status: str,
        violations: List[RuleStatus],
        critical_warnings: List[RuleStatus],
        warnings: List[RuleStatus],
    ) -> str:
        if overall_status == "violated":
            names = ", ".join(v.rule_name for v in violations)
            return f"ACCOUNT AT RISK: {names} violated. Stop trading immediately."
        if overall_status == "critical":
            names = ", ".join(c.rule_name for c in critical_warnings)
            return f"CRITICAL: {names} approaching limit. Reduce risk now."
        if overall_status == "warning":
            names = ", ".join(w.rule_name for w in warnings)
            return f"Caution: {names} above 70% usage. Monitor closely."
        return "All rules within safe limits. You are clear to trade."
