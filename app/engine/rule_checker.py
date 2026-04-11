"""
Rule Checker — evaluates user-defined trading rules against their trades.

Each rule type has a checker function that returns a list of violations.
Designed to run post-upload in background so it never blocks the user.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
from typing import Dict, List, Optional, Tuple

from app.models.trade import Trade
from app.models.trading_rule import TradingRule


class Violation:
    def __init__(self, rule: TradingRule, trade: Optional[Trade], message: str, severity: str = "warning"):
        self.rule = rule
        self.trade = trade
        self.message = message
        self.severity = severity


class RuleChecker:

    def check_all(
        self,
        trades: List[Trade],
        rules: List[TradingRule],
        tz_offset_hours: float = 0,
    ) -> List[Violation]:
        """Check all active rules against the trade list."""
        active_rules = [r for r in rules if r.is_active]
        if not active_rules or not trades:
            return []

        violations: List[Violation] = []
        for rule in active_rules:
            checker = self._get_checker(rule.rule_type)
            if checker:
                violations.extend(checker(trades, rule, tz_offset_hours))

        return violations

    def _get_checker(self, rule_type: str):
        checkers = {
            "max_trades_per_day": self._check_max_trades_per_day,
            "max_loss_per_day": self._check_max_loss_per_day,
            "max_loss_per_trade": self._check_max_loss_per_trade,
            "no_trading_after": self._check_no_trading_after,
            "no_trading_before": self._check_no_trading_before,
            "max_consecutive_losses": self._check_max_consecutive_losses,
            "max_position_size": self._check_max_position_size,
        }
        return checkers.get(rule_type)

    def _check_max_trades_per_day(
        self, trades: List[Trade], rule: TradingRule, tz_offset_hours: float
    ) -> List[Violation]:
        offset = timedelta(hours=tz_offset_hours)
        daily: Dict[str, List[Trade]] = defaultdict(list)
        for t in trades:
            day = (t.timestamp + offset).date().isoformat()
            daily[day].append(t)

        violations = []
        limit = int(rule.threshold)
        for day, day_trades in daily.items():
            if len(day_trades) > limit:
                excess = day_trades[limit:]
                for t in excess:
                    violations.append(Violation(
                        rule=rule,
                        trade=t,
                        message=f"Exceeded {limit} trades/day on {day} (took {len(day_trades)} trades)",
                        severity="warning",
                    ))
        return violations

    def _check_max_loss_per_day(
        self, trades: List[Trade], rule: TradingRule, tz_offset_hours: float
    ) -> List[Violation]:
        offset = timedelta(hours=tz_offset_hours)
        daily: Dict[str, List[Trade]] = defaultdict(list)
        for t in trades:
            day = (t.timestamp + offset).date().isoformat()
            daily[day].append(t)

        violations = []
        limit = rule.threshold
        for day, day_trades in daily.items():
            sorted_trades = sorted(day_trades, key=lambda t: t.timestamp)
            running_loss = 0.0
            breached = False
            for t in sorted_trades:
                if t.pnl < 0:
                    running_loss += abs(t.pnl)
                if running_loss > limit and not breached:
                    breached = True
                    violations.append(Violation(
                        rule=rule,
                        trade=t,
                        message=f"Daily loss limit of {limit} breached on {day} (total loss: {round(running_loss, 2)})",
                        severity="critical",
                    ))
                elif breached:
                    violations.append(Violation(
                        rule=rule,
                        trade=t,
                        message=f"Continued trading on {day} after daily loss limit was hit",
                        severity="critical",
                    ))
        return violations

    def _check_max_loss_per_trade(
        self, trades: List[Trade], rule: TradingRule, tz_offset_hours: float
    ) -> List[Violation]:
        violations = []
        limit = rule.threshold
        for t in trades:
            if t.pnl < 0 and abs(t.pnl) > limit:
                violations.append(Violation(
                    rule=rule,
                    trade=t,
                    message=f"Trade lost {round(abs(t.pnl), 2)} which exceeds max loss per trade of {limit}",
                    severity="warning",
                ))
        return violations

    def _check_no_trading_after(
        self, trades: List[Trade], rule: TradingRule, tz_offset_hours: float
    ) -> List[Violation]:
        offset = timedelta(hours=tz_offset_hours)
        cutoff_hour = int(rule.threshold)
        violations = []
        for t in trades:
            local_hour = (t.timestamp + offset).hour
            if local_hour >= cutoff_hour:
                violations.append(Violation(
                    rule=rule,
                    trade=t,
                    message=f"Trade at {(t.timestamp + offset).strftime('%H:%M')} violates no-trading-after {cutoff_hour}:00 rule",
                    severity="warning",
                ))
        return violations

    def _check_no_trading_before(
        self, trades: List[Trade], rule: TradingRule, tz_offset_hours: float
    ) -> List[Violation]:
        offset = timedelta(hours=tz_offset_hours)
        start_hour = int(rule.threshold)
        violations = []
        for t in trades:
            local_hour = (t.timestamp + offset).hour
            if local_hour < start_hour:
                violations.append(Violation(
                    rule=rule,
                    trade=t,
                    message=f"Trade at {(t.timestamp + offset).strftime('%H:%M')} violates no-trading-before {start_hour}:00 rule",
                    severity="warning",
                ))
        return violations

    def _check_max_consecutive_losses(
        self, trades: List[Trade], rule: TradingRule, tz_offset_hours: float
    ) -> List[Violation]:
        limit = int(rule.threshold)
        violations = []
        consec = 0
        for t in trades:
            if t.pnl < 0:
                consec += 1
                if consec > limit:
                    violations.append(Violation(
                        rule=rule,
                        trade=t,
                        message=f"Trade taken after {consec - 1} consecutive losses (limit: {limit})",
                        severity="critical",
                    ))
            else:
                consec = 0
        return violations

    def _check_max_position_size(
        self, trades: List[Trade], rule: TradingRule, tz_offset_hours: float
    ) -> List[Violation]:
        limit = rule.threshold
        violations = []
        for t in trades:
            if t.quantity > limit:
                violations.append(Violation(
                    rule=rule,
                    trade=t,
                    message=f"Position size {t.quantity} exceeds max allowed {limit}",
                    severity="warning",
                ))
        return violations


rule_checker = RuleChecker()
