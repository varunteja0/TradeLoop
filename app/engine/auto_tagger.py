"""
Auto-Tagger — rules-based inference of mood and mistake_category.

Runs post-upload. Only tags trades that don't already have a manual tag.
Trades are analyzed in chronological context: the meaning of a trade
depends on what happened before it (losses, streaks, timing, sizing).
"""
from __future__ import annotations

from datetime import timedelta
from typing import Dict, List, Optional, Tuple

from app.models.trade import Trade


class AutoTagger:

    REVENGE_GAP_SECONDS = 300  # trade within 5 min of a loss
    OVERSIZE_RATIO = 1.5       # position >1.5x average = oversized
    UNDERSIZE_RATIO = 0.5      # position <0.5x average = undersized

    def tag_trades(self, trades: List[Trade]) -> List[Tuple[str, Dict]]:
        """
        Analyze trades in order and return a list of (trade_id, updates) for trades
        that need auto-tags. Only tags trades where the field is currently None
        (preserves manual user input).
        """
        if len(trades) < 2:
            return []

        avg_qty = sum(t.quantity for t in trades) / len(trades)
        updates: List[Tuple[str, Dict]] = []

        for i, trade in enumerate(trades):
            mood_tag: Optional[str] = None
            mistake_tag: Optional[str] = None

            if i > 0:
                prev = trades[i - 1]
                gap = (trade.timestamp - prev.timestamp).total_seconds()

                # Revenge: trade taken < 5 min after a losing trade
                if prev.pnl < 0 and 0 < gap <= self.REVENGE_GAP_SECONDS:
                    mood_tag = "revenge"
                    mistake_tag = "revenge"

                # FOMO: sizing up significantly after seeing a winning trade
                if prev.pnl > 0 and trade.quantity > avg_qty * self.OVERSIZE_RATIO:
                    if mood_tag is None:
                        mood_tag = "fomo"

                # Tilt / anxiety: sizing up after consecutive losses
                consec_losses = self._consecutive_losses_before(trades, i)
                if consec_losses >= 2 and trade.quantity > trades[i - 1].quantity * 1.2:
                    if mood_tag is None:
                        mood_tag = "anxious"
                    mistake_tag = "oversized"

            # Oversized position (standalone check)
            if trade.quantity > avg_qty * self.OVERSIZE_RATIO and mistake_tag is None:
                mistake_tag = "oversized"

            # Undersized position
            if trade.quantity < avg_qty * self.UNDERSIZE_RATIO and mistake_tag is None:
                mistake_tag = "undersized"

            # Early exit heuristic: trade lost money with very short duration
            if (
                trade.duration_minutes is not None
                and trade.duration_minutes < 2
                and trade.pnl < 0
                and mistake_tag is None
            ):
                mistake_tag = "early_exit"

            # Winning trade with no detected issues → confident
            if trade.pnl > 0 and mood_tag is None:
                mood_tag = "confident"

            # Losing trade with no special context → neutral
            if trade.pnl < 0 and mood_tag is None:
                mood_tag = "neutral"

            # Rule followed: simple heuristic — no mistake detected
            rule_followed: Optional[bool] = None
            if mistake_tag is None or mistake_tag == "none":
                rule_followed = True
                mistake_tag = "none"
            else:
                rule_followed = False

            changes: Dict = {}
            if trade.mood is None and mood_tag is not None:
                changes["mood"] = mood_tag
            if trade.mistake_category is None and mistake_tag is not None:
                changes["mistake_category"] = mistake_tag
            if trade.rule_followed is None and rule_followed is not None:
                changes["rule_followed"] = rule_followed

            if changes:
                updates.append((trade.id, changes))

        return updates

    def _consecutive_losses_before(self, trades: List[Trade], index: int) -> int:
        count = 0
        for j in range(index - 1, -1, -1):
            if trades[j].pnl < 0:
                count += 1
            else:
                break
        return count


auto_tagger = AutoTagger()
