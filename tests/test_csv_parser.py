from __future__ import annotations

import pytest

from app.engine.csv_parser import parse_csv, validate_csv_size, _detect_format, MAX_FILE_SIZE


# =====================================================================
# Generic format parsing
# =====================================================================
class TestGenericFormat:

    def test_generic_format(self):
        csv_content = (
            "date,symbol,side,entry_price,exit_price,quantity,pnl,duration,fees,setup,notes\n"
            "2024-06-10 09:00:00,AAPL,BUY,150.0,155.0,10,50.0,30,2.0,breakout,good entry\n"
            "2024-06-10 10:00:00,TSLA,SELL,200.0,195.0,5,25.0,45,1.5,reversal,\n"
            "2024-06-10 11:00:00,MSFT,BUY,300.0,290.0,8,-80.0,20,3.0,,bad read\n"
        )
        trades, errors = parse_csv(csv_content, broker="generic")

        assert len(trades) == 3
        assert len(errors) == 0
        assert trades[0].symbol == "AAPL"
        assert trades[0].pnl == 50.0
        assert trades[0].fees == 2.0
        assert trades[0].duration_minutes == 30.0
        assert trades[0].setup_type == "breakout"
        assert trades[1].side == "SELL"
        assert trades[2].pnl == -80.0


# =====================================================================
# Auto-detection
# =====================================================================
class TestAutoDetect:

    def test_auto_detect_generic(self):
        csv_content = "date,symbol,side,entry_price,exit_price,quantity,pnl\n"
        fmt = _detect_format(csv_content)
        assert fmt == "generic"

    def test_auto_detect_zerodha(self):
        csv_content = "trade_date,tradingsymbol,exchange,segment,trade_type,quantity,price\n"
        fmt = _detect_format(csv_content)
        assert fmt == "zerodha"

    def test_auto_detect_mt4(self):
        csv_content = "Ticket,Open Time,Close Time,Type,Size,Symbol,Open Price,Close Price,Profit\n"
        fmt = _detect_format(csv_content)
        assert fmt == "mt4"


# =====================================================================
# Error handling
# =====================================================================
class TestErrorHandling:

    def test_missing_columns(self):
        """CSV with no recognizable date column — all rows should error."""
        csv_content = (
            "name,value\n"
            "foo,123\n"
            "bar,456\n"
        )
        trades, errors = parse_csv(csv_content, broker="generic")
        assert len(trades) == 0

    def test_invalid_timestamps(self):
        csv_content = (
            "date,symbol,side,entry_price,exit_price,quantity,pnl\n"
            "not-a-date,AAPL,BUY,150,155,10,50\n"
            "also-bad,TSLA,SELL,200,195,5,25\n"
            "2024-06-10,MSFT,BUY,300,290,8,-80\n"
        )
        trades, errors = parse_csv(csv_content, broker="generic")
        assert len(trades) == 1
        assert len(errors) == 2
        assert "invalid timestamp" in errors[0].lower()


# =====================================================================
# Accounting format
# =====================================================================
class TestAccountingFormat:

    def test_accounting_format(self):
        csv_content = (
            "date,symbol,side,entry_price,exit_price,quantity,pnl\n"
            "2024-06-10 09:00:00,AAPL,BUY,150.0,145.0,10,(500)\n"
        )
        trades, errors = parse_csv(csv_content, broker="generic")
        assert len(trades) == 1
        assert trades[0].pnl == -500.0


# =====================================================================
# File size validation
# =====================================================================
class TestFileSize:

    def test_file_size_limit(self):
        large_content = "x" * (MAX_FILE_SIZE + 1)
        result = validate_csv_size(large_content)
        assert result is not None
        assert "exceeds" in result.lower()

    def test_file_size_ok(self):
        small_content = "x" * 100
        result = validate_csv_size(small_content)
        assert result is None


# =====================================================================
# Empty CSV
# =====================================================================
class TestEmptyCsv:

    def test_empty_csv(self):
        trades, errors = parse_csv("", broker="generic")
        assert trades == []

    def test_header_only_csv(self):
        csv_content = "date,symbol,side,entry_price,exit_price,quantity,pnl\n"
        trades, errors = parse_csv(csv_content, broker="generic")
        assert trades == []


# =====================================================================
# Flexible / headerless / delimiter sniffing
# =====================================================================
class TestFlexibleImports:

    def test_headerless_broker_row_comma(self):
        """MT-style row with symbol, side, open date/time, prices, explicit PnL."""
        csv_content = (
            "USOIL,Sell,4/9/2026,20:52,101.8,4/9/2026,20:56,102.051,100.88,102.048,0.2,$0.00"
        )
        trades, errors = parse_csv(csv_content, broker="generic")
        assert len(errors) == 0
        assert len(trades) == 1
        assert trades[0].symbol == "USOIL"
        assert trades[0].side == "SELL"
        assert trades[0].pnl == 0.0
        assert trades[0].duration_minutes is not None

    def test_tab_separated_same_row(self):
        csv_content = (
            "USOIL\tSell\t4/9/2026\t20:52\t101.8\t4/9/2026\t20:56\t102.051\t0.2\t$0.00"
        )
        trades, errors = parse_csv(csv_content, broker="generic")
        assert len(errors) == 0
        assert len(trades) == 1
        assert trades[0].symbol == "USOIL"

    def test_utf8_bom_generic(self):
        csv_content = (
            "\ufeffdate,symbol,side,entry_price,exit_price,quantity,pnl\n"
            "2024-06-10 09:00:00,AAPL,BUY,150.0,155.0,10,50.0\n"
        )
        trades, errors = parse_csv(csv_content, broker="generic")
        assert len(errors) == 0
        assert len(trades) == 1
        assert trades[0].symbol == "AAPL"
