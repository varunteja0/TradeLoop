"""
Multi-broker CSV parser.

Supports: Generic format, Zerodha tradebook, MT4/MT5 statement.
Auto-detects format from column headers.
Returns normalized TradeCreate objects regardless of input,
along with a list of per-row error strings.
"""

from __future__ import annotations

import csv
import io
import re
from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional, Tuple

from app.schemas.trade import TradeCreate


BrokerFormat = Literal["generic", "zerodha", "mt4", "auto"]

MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5 MB


def validate_csv_size(content: str) -> Optional[str]:
    """Return an error string if *content* exceeds MAX_FILE_SIZE, else None."""
    if len(content.encode("utf-8")) > MAX_FILE_SIZE:
        return f"CSV content exceeds maximum allowed size of {MAX_FILE_SIZE} bytes"
    return None


def parse_csv(
    content: str, broker: BrokerFormat = "auto"
) -> Tuple[List[TradeCreate], List[str]]:
    """Parse *content* and return ``(trades, errors)``."""
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


def _parse_generic(content: str) -> Tuple[List[TradeCreate], List[str]]:
    """
    Expected columns (flexible naming):
    date/timestamp, symbol, side/direction, entry_price, exit_price, quantity/size, pnl/profit
    Optional: duration, setup, notes, fees
    """
    reader = csv.DictReader(io.StringIO(content))
    if reader.fieldnames is None:
        return [], []

    col_map = _build_column_map(reader.fieldnames)
    trades: List[TradeCreate] = []
    errors: List[str] = []

    for row_num, row in enumerate(reader, start=2):
        try:
            raw_ts = row.get(col_map.get("timestamp", ""), "")
            ts = _parse_timestamp(raw_ts)
            if ts is None:
                errors.append(f"Row {row_num}: invalid timestamp '{raw_ts}'")
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

            duration: Optional[float] = None
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
        except (ValueError, KeyError) as exc:
            errors.append(f"Row {row_num}: {exc}")
            continue

    return trades, errors


def _parse_zerodha(content: str) -> Tuple[List[TradeCreate], List[str]]:
    """
    Zerodha Console tradebook export format:
    trade_date, tradingsymbol, exchange, segment, trade_type, quantity, price, order_id, ...

    Zerodha exports individual legs, so we pair BUY/SELL for same symbol on same day.
    The leg that occurs first determines whether the trade is long (BUY first) or
    short (SELL first).  PnL is computed accordingly.
    """
    reader = csv.DictReader(io.StringIO(content))
    if reader.fieldnames is None:
        return [], []

    rows = list(reader)

    daily_trades: Dict[str, List[dict]] = {}
    for row in rows:
        row = {k.strip().lower(): v.strip() for k, v in row.items()}
        key = f"{row.get('trade_date', '')}-{row.get('tradingsymbol', '')}"
        if key not in daily_trades:
            daily_trades[key] = []
        daily_trades[key].append(row)

    trades: List[TradeCreate] = []
    errors: List[str] = []

    for key, group in daily_trades.items():
        buys = [r for r in group if r.get("trade_type", "").upper() == "BUY"]
        sells = [r for r in group if r.get("trade_type", "").upper() == "SELL"]

        pairs = min(len(buys), len(sells))
        for i in range(pairs):
            buy = buys[i]
            sell = sells[i]

            try:
                buy_ts = _parse_timestamp(buy.get("trade_date", ""))
                sell_ts = _parse_timestamp(sell.get("trade_date", ""))

                buy_time = _parse_timestamp(buy.get("order_execution_time", buy.get("trade_date", "")))
                sell_time = _parse_timestamp(sell.get("order_execution_time", sell.get("trade_date", "")))

                if buy_time is None and sell_time is None:
                    first_idx_buy = group.index(buy)
                    first_idx_sell = group.index(sell)
                    buy_first = first_idx_buy < first_idx_sell
                elif buy_time is None:
                    buy_first = False
                elif sell_time is None:
                    buy_first = True
                else:
                    buy_first = buy_time <= sell_time

                ts = buy_ts or sell_ts
                if ts is None:
                    errors.append(f"Zerodha group '{key}' pair {i}: invalid timestamp")
                    continue

                symbol = buy.get("tradingsymbol", sell.get("tradingsymbol", "UNKNOWN")).upper()
                buy_price = _parse_float(buy.get("price", "0"))
                sell_price = _parse_float(sell.get("price", "0"))
                qty = _parse_float(buy.get("quantity", "1"))

                if buy_first:
                    side = "BUY"
                    entry_price = buy_price
                    exit_price = sell_price
                    pnl = (exit_price - entry_price) * qty
                else:
                    side = "SELL"
                    entry_price = sell_price
                    exit_price = buy_price
                    pnl = (entry_price - exit_price) * qty

                trades.append(TradeCreate(
                    timestamp=ts,
                    symbol=symbol,
                    side=side,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    quantity=qty,
                    pnl=round(pnl, 2),
                    duration_minutes=None,
                    setup_type=None,
                    notes=None,
                    fees=0,
                ))
            except (ValueError, KeyError) as exc:
                errors.append(f"Zerodha group '{key}' pair {i}: {exc}")
                continue

    return trades, errors


def _parse_mt4(content: str) -> Tuple[List[TradeCreate], List[str]]:
    """
    MT4/MT5 CSV statement export:
    Ticket, Open Time, Close Time, Type, Size, Symbol, Open Price, Close Price, Commission, Swap, Profit
    """
    reader = csv.DictReader(io.StringIO(content))
    if reader.fieldnames is None:
        return [], []

    trades: List[TradeCreate] = []
    errors: List[str] = []

    for row_num, row in enumerate(reader, start=2):
        row_clean = {k.strip().lower(): v.strip() for k, v in row.items()}
        try:
            trade_type = row_clean.get("type", "").lower()
            if trade_type not in ("buy", "sell"):
                continue

            raw_open = row_clean.get("open time", row_clean.get("opentime", ""))
            open_time = _parse_timestamp(raw_open)
            raw_close = row_clean.get("close time", row_clean.get("closetime", ""))
            close_time = _parse_timestamp(raw_close)
            if open_time is None:
                errors.append(f"Row {row_num}: invalid open time '{raw_open}'")
                continue

            symbol = row_clean.get("symbol", row_clean.get("item", "UNKNOWN")).upper()
            entry = _parse_float(row_clean.get("open price", row_clean.get("openprice", "0")))
            exit_p = _parse_float(row_clean.get("close price", row_clean.get("closeprice", "0")))
            size = _parse_float(row_clean.get("size", row_clean.get("volume", "1")))

            commission = _parse_float(row_clean.get("commission", "0"))
            swap = _parse_float(row_clean.get("swap", "0"))
            profit = _parse_float(row_clean.get("profit", "0"))
            pnl = profit + commission + swap

            duration: Optional[float] = None
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
        except (ValueError, KeyError) as exc:
            errors.append(f"Row {row_num}: {exc}")
            continue

    return trades, errors


# ========================= HELPERS =========================

COLUMN_ALIASES: Dict[str, List[str]] = {
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


def _build_column_map(headers: List[str]) -> Dict[str, str]:
    """Map our canonical field names to actual CSV column names."""
    normalized = {h.strip().lower().replace(" ", "_"): h for h in headers}
    mapping: Dict[str, str] = {}

    for field, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in normalized:
                mapping[field] = normalized[alias]
                break

    return mapping


# Date format order:
#   1. ISO / unambiguous formats first (YYYY-prefixed).
#   2. Ambiguous day-first (dd/mm) before month-first (mm/dd).
#      This matches the Indian market convention (Zerodha, NSE, BSE).
_TIMESTAMP_FORMATS: List[str] = [
    # ISO / unambiguous (year first)
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
    "%Y.%m.%d %H:%M:%S",
    "%Y.%m.%d %H:%M",
    # Unambiguous day-first with dashes
    "%d-%m-%Y %H:%M:%S",
    "%d-%m-%Y",
    # Ambiguous slash-separated — dd/mm before mm/dd (Indian market preference)
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y",
]


def _parse_timestamp(value: str) -> Optional[datetime]:
    if not value or not value.strip():
        return None

    value = value.strip()

    for fmt in _TIMESTAMP_FORMATS:
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
    value = value.strip()
    # Accounting-style negatives: (500) -> -500
    if value.startswith('(') and value.endswith(')'):
        value = '-' + value[1:-1]
    cleaned = re.sub(r"[^\d.\-+eE]", "", value)
    try:
        return float(cleaned)
    except ValueError:
        return 0.0
