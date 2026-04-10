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
    content = _strip_bom(content)
    if broker == "auto":
        broker = _detect_format(content)

    delim = _detect_delimiter(content)

    parsers = {
        "generic": lambda c: _parse_generic(c, delimiter=delim),
        "zerodha": lambda c: _parse_zerodha(c, delimiter=delim),
        "mt4": lambda c: _parse_mt4(c, delimiter=delim),
    }

    parser = parsers.get(broker, parsers["generic"])
    return parser(content)


def _detect_format(content: str) -> BrokerFormat:
    first_lines = content[:1000].lower()

    if "trade_date" in first_lines or "tradingsymbol" in first_lines or "exchange" in first_lines:
        return "zerodha"
    if "ticket" in first_lines or "open time" in first_lines or "close time" in first_lines:
        return "mt4"
    return "generic"


def _strip_bom(content: str) -> str:
    if content.startswith("\ufeff"):
        return content[1:]
    return content


def _detect_delimiter(content: str) -> str:
    """Pick comma, tab, semicolon, or pipe using csv.Sniffer with sane fallbacks."""
    sample = content[:8192]
    if not sample.strip():
        return ","
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
        return dialect.delimiter
    except csv.Error:
        pass
    first_line = sample.splitlines()[0] if sample.splitlines() else ""
    tab_count = first_line.count("\t")
    comma_count = first_line.count(",")
    semi_count = first_line.count(";")
    if tab_count >= comma_count and tab_count >= semi_count and tab_count > 0:
        return "\t"
    if semi_count > comma_count:
        return ";"
    return ","


def _parse_generic(content: str, delimiter: str = ",") -> Tuple[List[TradeCreate], List[str]]:
    """
    Flexible parser: tries header matching first, then scans data to find
    date/symbol/pnl columns automatically. If no header row is detected,
    assigns positional column names and parses by data inspection.
    """
    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    if reader.fieldnames is None:
        return [], ["Could not read CSV headers. Make sure the file has a header row."]

    fieldnames = list(reader.fieldnames)

    # Detect if the "header" row is actually data (no recognized column names
    # AND first "header" value looks like a date or a ticker symbol)
    header_map = _build_column_map(fieldnames)
    first_fields = [f.strip() for f in fieldnames]
    header_looks_like_data = (
        len(header_map) <= 1
        and len(first_fields) >= 3
        and (
            _parse_timestamp(first_fields[0]) is not None
            or _parse_timestamp(" ".join(first_fields[:2])) is not None
            or any(_parse_timestamp(f) is not None for f in first_fields)
            or re.match(r"^[A-Z]{2,}[A-Z0-9]*$", first_fields[0])
        )
    )

    if header_looks_like_data:
        return _parse_headerless(content, delimiter=delimiter)

    all_rows = list(reader)
    if not all_rows:
        return [], ["CSV has headers but no data rows."]

    col_map = _build_column_map_smart(fieldnames, all_rows)

    if "timestamp" not in col_map:
        detected = ", ".join(fieldnames[:8])
        return [], [
            f"Could not find a date/timestamp column. "
            f"Your columns: [{detected}]. "
            f"Rename your date column to 'date' or 'timestamp' and re-upload."
        ]

    trades: List[TradeCreate] = []
    errors: List[str] = []

    for row_num, row in enumerate(all_rows, start=2):
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
            if side not in ("BUY", "SELL", "LONG", "SHORT"):
                side = "BUY"
            if side == "LONG":
                side = "BUY"
            if side == "SHORT":
                side = "SELL"

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


def _parse_zerodha(content: str, delimiter: str = ",") -> Tuple[List[TradeCreate], List[str]]:
    """
    Zerodha Console tradebook export format:
    trade_date, tradingsymbol, exchange, segment, trade_type, quantity, price, order_id, ...

    Zerodha exports individual legs, so we pair BUY/SELL for same symbol on same day.
    The leg that occurs first determines whether the trade is long (BUY first) or
    short (SELL first).  PnL is computed accordingly.
    """
    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
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


def _parse_mt4(content: str, delimiter: str = ",") -> Tuple[List[TradeCreate], List[str]]:
    """
    MT4/MT5 CSV statement export:
    Ticket, Open Time, Close Time, Type, Size, Symbol, Open Price, Close Price, Commission, Swap, Profit
    """
    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
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


def _is_time_only_cell(value: str) -> bool:
    v = value.strip()
    return bool(re.match(r"^\d{1,2}:\d{2}(:\d{2})?$", v))


def _find_date_time_pairs_in_row(row: List[str]) -> List[Tuple[int, int]]:
    """Indices (date_col, time_col) where date + adjacent time merge to a valid datetime."""
    pairs: List[Tuple[int, int]] = []
    for i in range(len(row) - 1):
        a, b = row[i].strip(), row[i + 1].strip()
        if not a or not b:
            continue
        if _parse_timestamp(a) is None:
            continue
        if not _is_time_only_cell(b):
            continue
        merged = _parse_timestamp(a + " " + b)
        if merged is not None:
            pairs.append((i, i + 1))
    return pairs


def _scan_row_for_datetime(row: List[str]) -> Optional[datetime]:
    """Last-resort: any single cell or two adjacent cells that parse as a timestamp."""
    for i, cell in enumerate(row):
        ts = _parse_timestamp(cell.strip())
        if ts is not None:
            return ts
    for i in range(len(row) - 1):
        ts = _parse_timestamp(row[i].strip() + " " + row[i + 1].strip())
        if ts is not None:
            return ts
    return None


def _explicit_pnl_from_row(row: List[str]) -> Optional[float]:
    """Prefer broker-style profit in a cell with a currency symbol."""
    for cell in reversed(row):
        if not cell or cell.strip() == "":
            continue
        if "$" in cell or "₹" in cell or "€" in cell or "£" in cell:
            return _parse_float(cell)
    return None


def _parse_loose_trade_row(row: List[str]) -> Optional[TradeCreate]:
    """
    Parse one trade from a headerless row by walking cells left-to-right:
    date+time pairs, symbol, side, prices, optional explicit PnL.
    """
    row = [c.strip() for c in row]
    if len(row) < 2:
        return None

    pairs = _find_date_time_pairs_in_row(row)
    paired_indices = {i for p in pairs for i in p}

    ts: Optional[datetime] = None
    duration_minutes: Optional[float] = None

    if pairs:
        open_dt = _parse_timestamp(row[pairs[0][0]] + " " + row[pairs[0][1]])
        if open_dt is None:
            return None
        ts = open_dt
        if len(pairs) >= 2:
            close_dt = _parse_timestamp(row[pairs[1][0]] + " " + row[pairs[1][1]])
            if close_dt is not None:
                duration_minutes = (close_dt - open_dt).total_seconds() / 60
    else:
        ts = _scan_row_for_datetime(row)

    if ts is None:
        return None

    symbol = "UNKNOWN"
    side = "BUY"
    side_col: Optional[int] = None

    for i, cell in enumerate(row):
        if i in paired_indices:
            continue
        u = cell.upper()
        if u in ("BUY", "SELL", "LONG", "SHORT"):
            side_col = i
            if u in ("SELL", "SHORT"):
                side = "SELL"
            elif u in ("BUY", "LONG"):
                side = "BUY"
            break

    for i, cell in enumerate(row):
        if i in paired_indices or i == side_col:
            continue
        if _parse_timestamp(cell) is not None or _is_time_only_cell(cell):
            continue
        sym = _guess_symbol_token(cell)
        if sym:
            symbol = sym
            break

    float_cells: List[Tuple[int, float]] = []
    for i, cell in enumerate(row):
        if i in paired_indices or i == side_col:
            continue
        if _parse_timestamp(cell) is not None or _is_time_only_cell(cell):
            continue
        if not re.search(r"\d", cell):
            continue
        f = _parse_float(cell)
        float_cells.append((i, f))

    explicit_pnl = _explicit_pnl_from_row(row)

    entry_price = 0.0
    exit_price = 0.0
    quantity = 1.0
    pnl = 0.0

    nums = [fv for _, fv in float_cells]
    if len(nums) >= 2:
        entry_price, exit_price = nums[0], nums[1]
    elif len(nums) == 1:
        entry_price = nums[0]

    if explicit_pnl is not None:
        pnl = round(explicit_pnl, 2)
    elif entry_price > 0 and exit_price > 0:
        if side == "BUY":
            pnl = round((exit_price - entry_price) * quantity, 2)
        else:
            pnl = round((entry_price - exit_price) * quantity, 2)
    elif len(nums) == 1:
        pnl = round(nums[0], 2)

    return TradeCreate(
        timestamp=ts,
        symbol=symbol,
        side=side,
        entry_price=entry_price,
        exit_price=exit_price,
        quantity=quantity,
        pnl=pnl,
        duration_minutes=round(duration_minutes, 1) if duration_minutes is not None else None,
        setup_type=None,
        notes=None,
        fees=0.0,
    )


def _guess_symbol_token(cell: str) -> Optional[str]:
    c = cell.strip()
    if not c or len(c) > 32:
        return None
    u = c.upper()
    if u in ("BUY", "SELL", "LONG", "SHORT", "UNKNOWN"):
        return None
    if re.match(r"^[A-Z$][A-Z0-9._$-]{1,24}$", c, re.I):
        return u
    return None


def _parse_headerless(content: str, delimiter: str = ",") -> Tuple[List[TradeCreate], List[str]]:
    """
    Parse a CSV that has no header row. Uses column heuristics first, then
    per-row adaptive parsing so varied broker exports still import.
    """
    rows = list(csv.reader(io.StringIO(content), delimiter=delimiter))
    if not rows:
        return [], ["Empty CSV file."]

    num_cols = len(rows[0])
    if num_cols < 2:
        return [], ["CSV has too few columns to infer a trade."]

    # Classify each column by scanning rows (threshold relaxed for sparse exports)
    date_cols: List[int] = []
    time_only_cols: List[int] = []
    symbol_col: Optional[int] = None
    side_col: Optional[int] = None
    numeric_cols: List[int] = []

    def _passes_ratio(count: int, n: int, ratio: float) -> bool:
        if n <= 0:
            return False
        return count >= max(1, int(n * ratio + 0.999))  # ceil(n * ratio), min 1

    for col_idx in range(num_cols):
        sample_vals = [r[col_idx].strip() for r in rows[:20] if col_idx < len(r) and r[col_idx].strip()]

        if not sample_vals:
            continue

        n = len(sample_vals)
        date_count = sum(1 for v in sample_vals if _parse_timestamp(v) is not None)
        time_only_count = sum(1 for v in sample_vals if _is_time_only_cell(v))
        side_count = sum(1 for v in sample_vals if v.upper() in ("BUY", "SELL", "LONG", "SHORT"))
        alpha_count = sum(
            1
            for v in sample_vals
            if re.match(r"^[A-Z][A-Z0-9]{1,20}$", v.upper())
            and v.upper() not in ("BUY", "SELL", "LONG", "SHORT")
        )
        num_count = sum(
            1 for v in sample_vals if re.match(r"^[\-\+\$₹€£]?[\d,.()]+$", v.replace(" ", ""))
        )

        ratio = 0.35
        if _passes_ratio(date_count, n, ratio):
            date_cols.append(col_idx)
        elif _passes_ratio(time_only_count, n, ratio):
            time_only_cols.append(col_idx)
        elif _passes_ratio(side_count, n, ratio):
            side_col = col_idx
        elif _passes_ratio(alpha_count, n, ratio) and symbol_col is None:
            symbol_col = col_idx
        elif _passes_ratio(num_count, n, ratio):
            numeric_cols.append(col_idx)

    merged_date_pairs: List[Tuple[int, int]] = []
    for dc in date_cols:
        for tc in time_only_cols:
            if tc == dc + 1:
                test_merged = rows[0][dc].strip() + " " + rows[0][tc].strip()
                if _parse_timestamp(test_merged) is not None:
                    merged_date_pairs.append((dc, tc))
                    break

    use_adaptive = not date_cols and not merged_date_pairs
    if use_adaptive:
        trades: List[TradeCreate] = []
        errors: List[str] = []
        for row_num, row in enumerate(rows, start=1):
            if not any(c.strip() for c in row):
                continue
            t = _parse_loose_trade_row(row)
            if t is not None:
                trades.append(t)
            else:
                preview = ", ".join(row[:12])
                errors.append(f"Row {row_num}: could not infer date/time from [{preview}]")
        if trades:
            return trades, errors
        if errors:
            return [], errors
        return [], ["No rows could be parsed as trades."]

    trades = []
    errors = []

    for row_num, row in enumerate(rows, start=1):
        if len(row) < 2:
            continue
        try:
            loose = _parse_loose_trade_row(row)
            if loose is not None:
                trades.append(loose)
                continue

            ts = None
            if merged_date_pairs:
                a, b = merged_date_pairs[0]
                if a < len(row) and b < len(row):
                    ts = _parse_timestamp(row[a].strip() + " " + row[b].strip())
            if ts is None and date_cols and date_cols[0] < len(row):
                ts = _parse_timestamp(row[date_cols[0]].strip())
            if ts is None:
                ts = _scan_row_for_datetime(row)
            if ts is None:
                errors.append(f"Row {row_num}: no parseable date found")
                continue

            symbol = (
                row[symbol_col].strip().upper()
                if symbol_col is not None and symbol_col < len(row)
                else "UNKNOWN"
            )

            side = "BUY"
            if side_col is not None and side_col < len(row):
                s = row[side_col].strip().upper()
                if s in ("SELL", "SHORT"):
                    side = "SELL"

            nums = [(_parse_float(row[ci]), ci) for ci in numeric_cols if ci < len(row)]
            num_vals = [n[0] for n in nums]

            entry_price = num_vals[0] if len(num_vals) >= 1 else 0.0
            exit_price = num_vals[1] if len(num_vals) >= 2 else 0.0
            quantity = 1.0
            pnl = 0.0

            explicit = _explicit_pnl_from_row(row)
            if explicit is not None:
                pnl = round(explicit, 2)
            elif entry_price > 0 and exit_price > 0:
                if side == "BUY":
                    pnl = round((exit_price - entry_price) * quantity, 2)
                else:
                    pnl = round((entry_price - exit_price) * quantity, 2)
            elif len(num_vals) == 1:
                pnl = round(num_vals[0], 2)

            trades.append(
                TradeCreate(
                    timestamp=ts,
                    symbol=symbol,
                    side=side,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    quantity=quantity,
                    pnl=pnl,
                    duration_minutes=None,
                    setup_type=None,
                    notes=None,
                    fees=0.0,
                )
            )
        except Exception as exc:
            errors.append(f"Row {row_num}: {exc}")
            continue

    return trades, errors


# ========================= HELPERS =========================

COLUMN_ALIASES: Dict[str, List[str]] = {
    "timestamp": [
        "date", "timestamp", "time", "datetime", "trade_date", "open_time",
        "entry_time", "close_time", "exit_time", "open_date", "close_date",
        "entry_date", "exit_date", "trade_time", "executed_at", "execution_time",
        "created_at", "filled_at", "order_time", "order_date",
    ],
    "symbol": [
        "symbol", "ticker", "instrument", "tradingsymbol", "pair", "asset",
        "stock", "scrip", "name", "security", "contract", "market",
        "trading_symbol", "script", "stock_name",
    ],
    "side": [
        "side", "direction", "type", "trade_type", "action", "buy_sell",
        "b/s", "bs", "order_type", "transaction_type", "buy/sell",
    ],
    "entry_price": [
        "entry_price", "entry", "open_price", "buy_price", "price_in",
        "avg_price", "average_price", "price", "fill_price", "executed_price",
    ],
    "exit_price": [
        "exit_price", "exit", "close_price", "sell_price", "price_out",
        "closing_price",
    ],
    "quantity": [
        "quantity", "qty", "size", "volume", "lots", "shares",
        "filled_qty", "traded_qty", "no_of_shares", "units",
    ],
    "pnl": [
        "pnl", "profit", "profit_loss", "p&l", "pl", "net_pnl", "realized_pnl",
        "realised_pnl", "gain", "gain_loss", "return", "net_profit",
        "profit/loss", "p/l", "gross_pnl", "total_pnl", "amount",
    ],
    "duration": ["duration", "duration_minutes", "hold_time", "holding_time"],
    "setup": ["setup", "setup_type", "strategy", "pattern", "tag", "label"],
    "notes": ["notes", "comment", "comments", "remarks", "description", "reason"],
    "fees": [
        "fees", "commission", "brokerage", "charges", "cost", "transaction_charges",
        "stt", "total_charges",
    ],
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


def _build_column_map_smart(
    headers: List[str], sample_rows: List[Dict[str, str]]
) -> Dict[str, str]:
    """
    Two-pass column mapping:
    1. Try header-name matching (existing logic)
    2. If timestamp column not found, scan sample data to find a column
       that contains parseable dates
    """
    mapping = _build_column_map(headers)

    if "timestamp" not in mapping and sample_rows:
        for h in headers:
            for row in sample_rows[:5]:
                val = row.get(h, "").strip()
                if val and _parse_timestamp(val) is not None:
                    mapping["timestamp"] = h
                    break
            if "timestamp" in mapping:
                break

    if "pnl" not in mapping and sample_rows:
        for h in headers:
            if h in [mapping.get(k) for k in mapping]:
                continue
            money_count = 0
            for row in sample_rows[:5]:
                val = row.get(h, "").strip()
                if val and ("$" in val or "₹" in val or re.match(r"^-?\d+\.?\d*$", val)):
                    money_count += 1
            if money_count >= 3:
                mapping["pnl"] = h
                break

    if "symbol" not in mapping and sample_rows:
        for h in headers:
            if h in [mapping.get(k) for k in mapping]:
                continue
            alpha_count = 0
            for row in sample_rows[:5]:
                val = row.get(h, "").strip()
                if val and re.match(r"^[A-Za-z]", val) and not _parse_timestamp(val):
                    alpha_count += 1
            if alpha_count >= 3:
                mapping["symbol"] = h
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
    # Ambiguous slash-separated — mm/dd first (broker exports typically use this)
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M",
    "%m/%d/%Y",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y",
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
