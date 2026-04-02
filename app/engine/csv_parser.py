"""
Multi-broker CSV parser.

Supports: Generic format, Zerodha tradebook, MT4/MT5 statement.
Auto-detects format from column headers.
Returns normalized TradeCreate objects regardless of input.
"""

from __future__ import annotations

import csv
import io
import re
from datetime import datetime, timezone
from typing import Literal

from app.schemas.trade import TradeCreate


BrokerFormat = Literal["generic", "zerodha", "mt4", "auto"]


def parse_csv(content: str, broker: BrokerFormat = "auto") -> list[TradeCreate]:
    if broker == "auto":
        broker = _detect_format(content)

    parsers = {
        "generic": _parse_generic,
        "zerodha": _parse_zerodha,
        "mt4": _parse_mt4,
    }

    parser = parsers.get(broker, _parse_generic)
    return parser(content)


def _detect_format(content: str) -> BrokerFormat:
    first_lines = content[:1000].lower()

    if "trade_date" in first_lines or "tradingsymbol" in first_lines or "exchange" in first_lines:
        return "zerodha"
    if "ticket" in first_lines or "open time" in first_lines or "close time" in first_lines:
        return "mt4"
    return "generic"


def _parse_generic(content: str) -> list[TradeCreate]:
    """
    Expected columns (flexible naming):
    date/timestamp, symbol, side/direction, entry_price, exit_price, quantity/size, pnl/profit
    Optional: duration, setup, notes, fees
    """
    reader = csv.DictReader(io.StringIO(content))
    if reader.fieldnames is None:
        return []

    col_map = _build_column_map(reader.fieldnames)
    trades = []

    for row in reader:
        try:
            ts = _parse_timestamp(row.get(col_map.get("timestamp", ""), ""))
            if ts is None:
                continue

            pnl_raw = row.get(col_map.get("pnl", ""), "0")
            pnl = _parse_float(pnl_raw)

            entry = _parse_float(row.get(col_map.get("entry_price", ""), "0"))
            exit_p = _parse_float(row.get(col_map.get("exit_price", ""), "0"))
            qty = _parse_float(row.get(col_map.get("quantity", ""), "1"))
            side = row.get(col_map.get("side", ""), "BUY").strip().upper()
            if side not in ("BUY", "SELL"):
                side = "BUY"

            symbol = row.get(col_map.get("symbol", ""), "UNKNOWN").strip().upper()

            duration = None
            if "duration" in col_map:
                dur_val = row.get(col_map["duration"], "")
                if dur_val:
                    duration = _parse_float(dur_val)

            fees = 0.0
            if "fees" in col_map:
                fees = _parse_float(row.get(col_map["fees"], "0"))

            setup = row.get(col_map.get("setup", ""), None)
            notes = row.get(col_map.get("notes", ""), None)

            trades.append(TradeCreate(
                timestamp=ts,
                symbol=symbol,
                side=side,
                entry_price=entry,
                exit_price=exit_p,
                quantity=qty,
                pnl=pnl,
                duration_minutes=duration,
                setup_type=setup if setup else None,
                notes=notes if notes else None,
                fees=fees,
            ))
        except (ValueError, KeyError):
            continue

    return trades


def _parse_zerodha(content: str) -> list[TradeCreate]:
    """
    Zerodha Console tradebook export format:
    trade_date, tradingsymbol, exchange, segment, trade_type, quantity, price, order_id, ...
    
    Zerodha exports individual legs, so we pair BUY/SELL for same symbol on same day.
    """
    reader = csv.DictReader(io.StringIO(content))
    if reader.fieldnames is None:
        return []

    cols = [c.strip().lower() for c in reader.fieldnames]
    rows = list(reader)

    daily_trades: dict[str, list[dict]] = {}
    for row in rows:
        row = {k.strip().lower(): v.strip() for k, v in row.items()}
        key = f"{row.get('trade_date', '')}-{row.get('tradingsymbol', '')}"
        if key not in daily_trades:
            daily_trades[key] = []
        daily_trades[key].append(row)

    trades = []
    processed = set()

    for key, group in daily_trades.items():
        buys = [r for r in group if r.get("trade_type", "").upper() == "BUY"]
        sells = [r for r in group if r.get("trade_type", "").upper() == "SELL"]

        pairs = min(len(buys), len(sells))
        for i in range(pairs):
            buy = buys[i]
            sell = sells[i]

            try:
                ts = _parse_timestamp(buy.get("trade_date", ""))
                if ts is None:
                    continue

                symbol = buy.get("tradingsymbol", "UNKNOWN").upper()
                entry_price = _parse_float(buy.get("price", "0"))
                exit_price = _parse_float(sell.get("price", "0"))
                qty = _parse_float(buy.get("quantity", "1"))
                pnl = (exit_price - entry_price) * qty

                trades.append(TradeCreate(
                    timestamp=ts,
                    symbol=symbol,
                    side="BUY",
                    entry_price=entry_price,
                    exit_price=exit_price,
                    quantity=qty,
                    pnl=round(pnl, 2),
                    duration_minutes=None,
                    setup_type=None,
                    notes=None,
                    fees=0,
                ))
            except (ValueError, KeyError):
                continue

    return trades


def _parse_mt4(content: str) -> list[TradeCreate]:
    """
    MT4/MT5 CSV statement export:
    Ticket, Open Time, Close Time, Type, Size, Symbol, Open Price, Close Price, Commission, Swap, Profit
    """
    reader = csv.DictReader(io.StringIO(content))
    if reader.fieldnames is None:
        return []

    trades = []
    for row in reader:
        row_clean = {k.strip().lower(): v.strip() for k, v in row.items()}
        try:
            trade_type = row_clean.get("type", "").lower()
            if trade_type not in ("buy", "sell"):
                continue

            open_time = _parse_timestamp(row_clean.get("open time", row_clean.get("opentime", "")))
            close_time = _parse_timestamp(row_clean.get("close time", row_clean.get("closetime", "")))
            if open_time is None:
                continue

            symbol = row_clean.get("symbol", row_clean.get("item", "UNKNOWN")).upper()
            entry = _parse_float(row_clean.get("open price", row_clean.get("openprice", "0")))
            exit_p = _parse_float(row_clean.get("close price", row_clean.get("closeprice", "0")))
            size = _parse_float(row_clean.get("size", row_clean.get("volume", "1")))

            commission = _parse_float(row_clean.get("commission", "0"))
            swap = _parse_float(row_clean.get("swap", "0"))
            profit = _parse_float(row_clean.get("profit", "0"))
            pnl = profit + commission + swap

            duration = None
            if open_time and close_time:
                duration = (close_time - open_time).total_seconds() / 60

            trades.append(TradeCreate(
                timestamp=open_time,
                symbol=symbol,
                side=trade_type.upper(),
                entry_price=entry,
                exit_price=exit_p,
                quantity=size,
                pnl=round(pnl, 2),
                duration_minutes=round(duration, 1) if duration else None,
                setup_type=None,
                notes=None,
                fees=abs(commission) + abs(swap),
            ))
        except (ValueError, KeyError):
            continue

    return trades


# ========================= HELPERS =========================

COLUMN_ALIASES = {
    "timestamp": ["date", "timestamp", "time", "datetime", "trade_date", "open_time", "entry_time"],
    "symbol": ["symbol", "ticker", "instrument", "tradingsymbol", "pair", "asset"],
    "side": ["side", "direction", "type", "trade_type", "action", "buy_sell"],
    "entry_price": ["entry_price", "entry", "open_price", "buy_price", "price_in"],
    "exit_price": ["exit_price", "exit", "close_price", "sell_price", "price_out"],
    "quantity": ["quantity", "qty", "size", "volume", "lots", "shares"],
    "pnl": ["pnl", "profit", "profit_loss", "p&l", "pl", "net_pnl", "realized_pnl"],
    "duration": ["duration", "duration_minutes", "hold_time", "holding_time"],
    "setup": ["setup", "setup_type", "strategy", "pattern"],
    "notes": ["notes", "comment", "comments", "remarks"],
    "fees": ["fees", "commission", "brokerage", "charges"],
}


def _build_column_map(headers: list[str]) -> dict[str, str]:
    """Map our canonical field names to actual CSV column names."""
    normalized = {h.strip().lower().replace(" ", "_"): h for h in headers}
    mapping = {}

    for field, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in normalized:
                mapping[field] = normalized[alias]
                break

    return mapping


def _parse_timestamp(value: str) -> datetime | None:
    if not value or not value.strip():
        return None

    value = value.strip()
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y",
        "%Y.%m.%d %H:%M:%S",
        "%Y.%m.%d %H:%M",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(value, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue

    return None


def _parse_float(value: str) -> float:
    if not value or not value.strip():
        return 0.0
    cleaned = re.sub(r"[^\d.\-+eE]", "", value.strip())
    try:
        return float(cleaned)
    except ValueError:
        return 0.0
