"""
Synthetic Trade Generator — generates realistic trader behavior for demos and testing.

Simulates real behavioral patterns:
  - Revenge trading (fast trades after losses)
  - Overtrading (burst days)
  - Risk mismanagement (position sizing errors)
  - Winning/losing streaks
  - Time-of-day patterns
  - Tilt (sizing up after losses)

Each scenario produces trades that the behavioral engine can detect,
making it perfect for demos, onboarding, and testing.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from app.schemas.trade import TradeCreate

SYMBOLS = ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "INFY", "HDFCBANK", "SBIN", "TATAMOTORS", "ICICIBANK", "ITC"]
SETUPS = ["breakout", "pullback", "mean_reversion", "momentum", "scalp", "swing", "gap_fill"]


class SyntheticGenerator:

    def generate(
        self,
        scenario: str = "mixed",
        num_trades: int = 100,
        base_date: Optional[datetime] = None,
        seed: Optional[int] = None,
    ) -> List[TradeCreate]:
        """Generate synthetic trades for a given scenario."""
        if seed is not None:
            random.seed(seed)

        if base_date is None:
            base_date = datetime.now(timezone.utc) - timedelta(days=30)

        generators = {
            "mixed": self._mixed_scenario,
            "revenge_heavy": self._revenge_heavy,
            "overtrading": self._overtrading,
            "disciplined": self._disciplined,
            "losing_streak": self._losing_streak,
            "risk_mismanagement": self._risk_mismanagement,
            "improving": self._improving_trader,
        }

        generator = generators.get(scenario, self._mixed_scenario)
        trades = generator(num_trades, base_date)
        trades.sort(key=lambda t: t.timestamp)
        return trades

    def _mixed_scenario(self, n: int, base: datetime) -> List[TradeCreate]:
        """Realistic mix of good and bad behavior."""
        trades = []
        current = base
        win_rate = 0.52
        consec_losses = 0

        for i in range(n):
            current += timedelta(minutes=random.randint(15, 480))
            if current.weekday() >= 5:
                current += timedelta(days=2)

            is_revenge = consec_losses >= 2 and random.random() < 0.4
            if is_revenge:
                current = trades[-1].timestamp + timedelta(minutes=random.randint(1, 4))

            symbol = random.choice(SYMBOLS)
            side = random.choice(["BUY", "SELL"])
            entry = round(random.uniform(100, 5000), 2)
            qty = round(random.uniform(1, 50), 0)

            if is_revenge:
                qty *= random.uniform(1.5, 2.5)
                actual_wr = win_rate * 0.6
            else:
                actual_wr = win_rate

            is_win = random.random() < actual_wr
            pnl_magnitude = random.uniform(50, 2000)
            pnl = round(pnl_magnitude if is_win else -pnl_magnitude, 2)

            if is_win:
                exit_p = entry + (pnl / max(qty, 1)) if side == "BUY" else entry - (pnl / max(qty, 1))
                consec_losses = 0
            else:
                exit_p = entry - (abs(pnl) / max(qty, 1)) if side == "BUY" else entry + (abs(pnl) / max(qty, 1))
                consec_losses += 1

            mood = None
            mistake = None
            if is_revenge:
                mood = "revenge"
                mistake = "revenge"
            elif qty > 40:
                mood = "fomo"
                mistake = "oversized"

            trades.append(TradeCreate(
                timestamp=current,
                symbol=symbol,
                side=side,
                entry_price=round(entry, 2),
                exit_price=round(max(exit_p, 0.01), 2),
                quantity=round(qty),
                pnl=pnl,
                duration_minutes=round(random.uniform(2, 180), 1),
                setup_type=random.choice(SETUPS),
                fees=round(random.uniform(5, 50), 2),
                mood=mood,
                mistake_category=mistake,
            ))

        return trades

    def _revenge_heavy(self, n: int, base: datetime) -> List[TradeCreate]:
        """Trader who revenge trades heavily — 30%+ trades are revenge."""
        trades = []
        current = base

        for i in range(n):
            current += timedelta(minutes=random.randint(20, 300))
            if current.weekday() >= 5:
                current += timedelta(days=2)

            symbol = random.choice(SYMBOLS[:5])
            side = random.choice(["BUY", "SELL"])
            entry = round(random.uniform(200, 3000), 2)
            qty = round(random.uniform(5, 30))

            is_win = random.random() < 0.50
            pnl = round(random.uniform(100, 1500) * (1 if is_win else -1), 2)
            exit_p = entry + (pnl / max(qty, 1)) if side == "BUY" else entry - (pnl / max(qty, 1))

            trades.append(TradeCreate(
                timestamp=current,
                symbol=symbol, side=side,
                entry_price=round(entry, 2), exit_price=round(max(exit_p, 0.01), 2),
                quantity=qty, pnl=pnl,
                duration_minutes=round(random.uniform(3, 120), 1),
                setup_type=random.choice(SETUPS), fees=round(random.uniform(5, 30), 2),
            ))

            if pnl < 0 and random.random() < 0.6:
                revenge_time = current + timedelta(minutes=random.randint(1, 4))
                revenge_qty = qty * random.uniform(1.3, 2.0)
                revenge_pnl = round(random.uniform(100, 800) * (1 if random.random() < 0.3 else -1), 2)
                revenge_entry = round(random.uniform(200, 3000), 2)
                revenge_exit = revenge_entry + (revenge_pnl / max(revenge_qty, 1))

                trades.append(TradeCreate(
                    timestamp=revenge_time,
                    symbol=symbol, side=side,
                    entry_price=round(revenge_entry, 2),
                    exit_price=round(max(revenge_exit, 0.01), 2),
                    quantity=round(revenge_qty), pnl=revenge_pnl,
                    duration_minutes=round(random.uniform(1, 15), 1),
                    setup_type=None, fees=round(random.uniform(5, 30), 2),
                    mood="revenge", mistake_category="revenge",
                ))

        return trades

    def _overtrading(self, n: int, base: datetime) -> List[TradeCreate]:
        """Trader who overtrades — some days have 15+ trades."""
        trades = []
        current = base
        day_count = 0

        while len(trades) < n:
            if current.weekday() >= 5:
                current += timedelta(days=2)

            is_binge_day = random.random() < 0.3
            day_trades = random.randint(12, 20) if is_binge_day else random.randint(2, 5)
            day_trades = min(day_trades, n - len(trades))

            market_open = current.replace(hour=9, minute=15, second=0)

            for j in range(day_trades):
                trade_time = market_open + timedelta(minutes=random.randint(0, 375))
                symbol = random.choice(SYMBOLS)
                entry = round(random.uniform(100, 4000), 2)
                qty = round(random.uniform(5, 25))

                wr = 0.40 if is_binge_day else 0.55
                is_win = random.random() < wr
                pnl = round(random.uniform(50, 800) * (1 if is_win else -1), 2)
                exit_p = entry + (pnl / max(qty, 1))

                trades.append(TradeCreate(
                    timestamp=trade_time,
                    symbol=symbol, side=random.choice(["BUY", "SELL"]),
                    entry_price=round(entry, 2), exit_price=round(max(exit_p, 0.01), 2),
                    quantity=qty, pnl=pnl,
                    duration_minutes=round(random.uniform(1, 60), 1),
                    setup_type=random.choice(SETUPS) if not is_binge_day else None,
                    fees=round(random.uniform(5, 25), 2),
                ))

            current += timedelta(days=1)
            day_count += 1

        return trades[:n]

    def _disciplined(self, n: int, base: datetime) -> List[TradeCreate]:
        """Well-disciplined trader — high win rate, consistent sizing, few mistakes."""
        trades = []
        current = base

        for i in range(n):
            current += timedelta(minutes=random.randint(60, 480))
            if current.weekday() >= 5:
                current += timedelta(days=2)

            symbol = random.choice(SYMBOLS[:6])
            entry = round(random.uniform(500, 3000), 2)
            qty = round(random.uniform(8, 15))

            is_win = random.random() < 0.62
            pnl = round(random.uniform(200, 1200) * (1 if is_win else -0.7), 2)
            exit_p = entry + (pnl / max(qty, 1))

            trades.append(TradeCreate(
                timestamp=current,
                symbol=symbol, side=random.choice(["BUY", "SELL"]),
                entry_price=round(entry, 2), exit_price=round(max(exit_p, 0.01), 2),
                quantity=qty, pnl=pnl,
                duration_minutes=round(random.uniform(15, 240), 1),
                setup_type=random.choice(SETUPS[:4]),
                fees=round(random.uniform(10, 30), 2),
                mood="confident" if is_win else "calm",
                mistake_category="none",
            ))

        return trades

    def _losing_streak(self, n: int, base: datetime) -> List[TradeCreate]:
        """Trader going through a drawdown with tilt behavior."""
        trades = []
        current = base
        streak_phase = 0.0

        for i in range(n):
            current += timedelta(minutes=random.randint(30, 300))
            if current.weekday() >= 5:
                current += timedelta(days=2)

            streak_phase = i / n
            if streak_phase < 0.3:
                wr = 0.55
            elif streak_phase < 0.7:
                wr = 0.30
            else:
                wr = 0.50

            symbol = random.choice(SYMBOLS)
            entry = round(random.uniform(200, 2000), 2)
            base_qty = 10
            qty = base_qty * (1 + streak_phase * 1.5) if 0.3 < streak_phase < 0.7 else base_qty
            qty = round(qty)

            is_win = random.random() < wr
            pnl = round(random.uniform(100, 1500) * (1 if is_win else -1), 2)
            exit_p = entry + (pnl / max(qty, 1))

            trades.append(TradeCreate(
                timestamp=current,
                symbol=symbol, side=random.choice(["BUY", "SELL"]),
                entry_price=round(entry, 2), exit_price=round(max(exit_p, 0.01), 2),
                quantity=qty, pnl=pnl,
                duration_minutes=round(random.uniform(5, 120), 1),
                setup_type=random.choice(SETUPS),
                fees=round(random.uniform(5, 30), 2),
            ))

        return trades

    def _risk_mismanagement(self, n: int, base: datetime) -> List[TradeCreate]:
        """Trader with wild position sizing — no risk management."""
        trades = []
        current = base

        for i in range(n):
            current += timedelta(minutes=random.randint(30, 360))
            if current.weekday() >= 5:
                current += timedelta(days=2)

            symbol = random.choice(SYMBOLS)
            entry = round(random.uniform(100, 3000), 2)
            qty = round(random.choice([
                random.uniform(1, 5),
                random.uniform(10, 20),
                random.uniform(50, 100),
                random.uniform(100, 200),
            ]))

            is_win = random.random() < 0.48
            pnl = round(random.uniform(50, 3000) * (1 if is_win else -1), 2)
            exit_p = entry + (pnl / max(qty, 1))

            trades.append(TradeCreate(
                timestamp=current,
                symbol=symbol, side=random.choice(["BUY", "SELL"]),
                entry_price=round(entry, 2), exit_price=round(max(exit_p, 0.01), 2),
                quantity=max(qty, 1), pnl=pnl,
                duration_minutes=round(random.uniform(1, 300), 1),
                setup_type=random.choice(SETUPS) if random.random() < 0.5 else None,
                fees=round(random.uniform(5, 50), 2),
                mistake_category="oversized" if qty > 50 else None,
            ))

        return trades

    def _improving_trader(self, n: int, base: datetime) -> List[TradeCreate]:
        """Trader who starts bad but gradually improves — great for demos."""
        trades = []
        current = base

        for i in range(n):
            current += timedelta(minutes=random.randint(30, 480))
            if current.weekday() >= 5:
                current += timedelta(days=2)

            progress = i / n
            wr = 0.35 + (progress * 0.25)
            avg_qty = 10 + (5 if progress < 0.3 else 0)
            revenge_prob = max(0, 0.3 - progress * 0.3)

            symbol = random.choice(SYMBOLS)
            entry = round(random.uniform(200, 2500), 2)
            qty = round(random.gauss(avg_qty, avg_qty * 0.3))
            qty = max(1, qty)

            is_revenge = (
                len(trades) > 0
                and trades[-1].pnl < 0
                and random.random() < revenge_prob
            )
            if is_revenge:
                current = trades[-1].timestamp + timedelta(minutes=random.randint(1, 4))
                qty = round(qty * 1.5)

            is_win = random.random() < (wr * 0.5 if is_revenge else wr)
            pnl = round(random.uniform(100, 1200) * (1 if is_win else -1), 2)
            exit_p = entry + (pnl / max(qty, 1))

            mood = None
            mistake = None
            if is_revenge:
                mood = "revenge"
                mistake = "revenge"
            elif progress > 0.7 and is_win:
                mood = "confident"
                mistake = "none"

            trades.append(TradeCreate(
                timestamp=current,
                symbol=symbol, side=random.choice(["BUY", "SELL"]),
                entry_price=round(entry, 2), exit_price=round(max(exit_p, 0.01), 2),
                quantity=qty, pnl=pnl,
                duration_minutes=round(random.uniform(5, 180), 1),
                setup_type=random.choice(SETUPS[:3]) if progress > 0.4 else None,
                fees=round(random.uniform(5, 30), 2),
                mood=mood, mistake_category=mistake,
            ))

        return trades


synthetic_generator = SyntheticGenerator()
