"""
Broker Sync Engine — converts raw orders into matched trades.

Zerodha and Angel One provide order-level data. We reconstruct
complete trades by matching entry orders with exit orders for the
same symbol on the same day.
"""
from __future__ import annotations
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger("tradeloop.broker_sync")

@dataclass
class RawOrder:
    """Normalized order from any broker."""
    order_id: str
    symbol: str
    side: str  # "BUY" or "SELL"
    quantity: float
    price: float
    timestamp: datetime
    status: str  # "COMPLETE", "CANCELLED", etc.
    exchange: str = ""
    fees: float = 0.0

@dataclass
class ReconstructedTrade:
    """A complete trade reconstructed from matched orders."""
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    entry_time: datetime
    exit_time: datetime
    duration_minutes: float
    fees: float
    source: str  # "zerodha", "angelone"


class OrderMatcher:
    """Match buy and sell orders into complete round-trip trades."""

    def match_orders(self, orders: List[RawOrder], source: str = "zerodha") -> List[ReconstructedTrade]:
        """Match orders into trades. Group by symbol and day, pair entries with exits."""
        completed = [o for o in orders if o.status.upper() in ("COMPLETE", "EXECUTED", "FILLED")]
        if not completed:
            return []

        by_symbol: Dict[str, List[RawOrder]] = defaultdict(list)
        for o in completed:
            by_symbol[o.symbol].append(o)

        trades: List[ReconstructedTrade] = []
        for symbol, sym_orders in by_symbol.items():
            sym_orders.sort(key=lambda o: o.timestamp)
            trades.extend(self._match_symbol_orders(sym_orders, source))

        trades.sort(key=lambda t: t.entry_time)
        logger.info("Matched %d trades from %d orders", len(trades), len(completed))
        return trades

    def _match_symbol_orders(self, orders: List[RawOrder], source: str) -> List[ReconstructedTrade]:
        """FIFO matching for a single symbol."""
        buys: list = []
        sells: list = []
        trades: List[ReconstructedTrade] = []

        for o in orders:
            if o.side == "BUY":
                buys.append(o)
            else:
                sells.append(o)

            while buys and sells:
                buy = buys[0]
                sell = sells[0]
                qty = min(buy.quantity, sell.quantity)

                if buy.timestamp <= sell.timestamp:
                    entry, exit_o = buy, sell
                    side = "BUY"
                else:
                    entry, exit_o = sell, buy
                    side = "SELL"

                pnl = (exit_o.price - entry.price) * qty if side == "BUY" else (entry.price - exit_o.price) * qty
                duration = (exit_o.timestamp - entry.timestamp).total_seconds() / 60

                trades.append(ReconstructedTrade(
                    symbol=entry.symbol,
                    side=side,
                    entry_price=entry.price,
                    exit_price=exit_o.price,
                    quantity=qty,
                    pnl=round(pnl, 2),
                    entry_time=entry.timestamp,
                    exit_time=exit_o.timestamp,
                    duration_minutes=round(duration, 1),
                    fees=round((entry.fees + exit_o.fees) * qty / max(entry.quantity, 1), 2),
                    source=source,
                ))

                buy.quantity -= qty
                sell.quantity -= qty
                if buy.quantity <= 0:
                    buys.pop(0)
                if sell.quantity <= 0:
                    sells.pop(0)

        return trades


def normalize_zerodha_orders(raw_data: List[dict]) -> List[RawOrder]:
    """Convert Zerodha Kite Connect /orders response to RawOrder objects."""
    orders: List[RawOrder] = []
    for o in raw_data:
        if o.get("status", "").upper() not in ("COMPLETE", "EXECUTED"):
            continue
        try:
            ts = datetime.fromisoformat(o.get("order_timestamp", o.get("exchange_timestamp", "")))
        except (ValueError, TypeError):
            continue

        orders.append(RawOrder(
            order_id=str(o.get("order_id", "")),
            symbol=o.get("tradingsymbol", o.get("trading_symbol", "UNKNOWN")),
            side=o.get("transaction_type", "BUY").upper(),
            quantity=float(o.get("filled_quantity", o.get("quantity", 0))),
            price=float(o.get("average_price", o.get("price", 0))),
            timestamp=ts,
            status="COMPLETE",
            exchange=o.get("exchange", ""),
            fees=0.0,
        ))
    return orders


def normalize_angelone_orders(raw_data: List[dict]) -> List[RawOrder]:
    """Convert Angel One SmartAPI /orderBook response to RawOrder objects."""
    orders: List[RawOrder] = []
    for o in raw_data:
        if o.get("orderstatus", "").lower() != "complete":
            continue
        try:
            ts_str = o.get("updatetime", o.get("exchtime", ""))
            ts = datetime.strptime(ts_str, "%d-%b-%Y %H:%M:%S") if ts_str else datetime.now(timezone.utc)
            ts = ts.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue

        orders.append(RawOrder(
            order_id=str(o.get("orderid", "")),
            symbol=o.get("tradingsymbol", "UNKNOWN"),
            side="BUY" if o.get("transactiontype", "").upper() == "BUY" else "SELL",
            quantity=float(o.get("filledshares", o.get("quantity", 0))),
            price=float(o.get("averageprice", o.get("price", 0))),
            timestamp=ts,
            status="COMPLETE",
            exchange=o.get("exchange", ""),
            fees=0.0,
        ))
    return orders
