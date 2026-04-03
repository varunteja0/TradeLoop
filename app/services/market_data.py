"""
Market Data Service — fetch historical OHLC for trade replay.

Uses Yahoo Finance (free, no API key). Falls back to synthetic data
if Yahoo is unavailable or symbol not found.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("tradeloop.market_data")

SYMBOL_MAP: Dict[str, str] = {
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "INFY": "INFY.NS",
    "SBIN": "SBIN.NS",
    "ITC": "ITC.NS",
    "WIPRO": "WIPRO.NS",
    "TATAMOTORS": "TATAMOTORS.NS",
    "NIFTY50": "^NSEI",
    "NIFTY": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
    "BTCUSD": "BTC-USD",
    "ETHUSD": "ETH-USD",
}


class OHLCCandle:
    __slots__ = ("timestamp", "open", "high", "low", "close", "volume")

    def __init__(self, timestamp: int, o: float, h: float, l: float, c: float, v: int = 0):
        self.timestamp = timestamp
        self.open = o
        self.high = h
        self.low = l
        self.close = c
        self.volume = v

    def to_dict(self) -> dict:
        return {
            "time": self.timestamp,
            "open": round(self.open, 2),
            "high": round(self.high, 2),
            "low": round(self.low, 2),
            "close": round(self.close, 2),
            "volume": self.volume,
        }


class MarketDataService:

    async def get_ohlc(
        self,
        symbol: str,
        trade_date: datetime,
        interval: str = "5m",
        hours_before: int = 1,
        hours_after: int = 2,
    ) -> List[dict]:
        """
        Fetch OHLC candles around a trade timestamp.

        Returns candles from (trade_time - hours_before) to (trade_time + hours_after).
        This shows the market context: what happened before, during, and after the trade.
        """
        yahoo_symbol = SYMBOL_MAP.get(symbol.upper(), f"{symbol.upper()}.NS")

        start = trade_date - timedelta(hours=hours_before)
        end = trade_date + timedelta(hours=hours_after)

        period1 = int(start.timestamp())
        period2 = int(end.timestamp())

        candles = await self._fetch_yahoo(yahoo_symbol, period1, period2, interval)

        if not candles:
            if yahoo_symbol.endswith(".NS"):
                candles = await self._fetch_yahoo(yahoo_symbol[:-3], period1, period2, interval)

        if not candles:
            logger.warning("No OHLC data for %s, generating synthetic", symbol)
            candles = self._generate_synthetic(trade_date, hours_before, hours_after, interval)

        return candles

    async def _fetch_yahoo(
        self, symbol: str, period1: int, period2: int, interval: str
    ) -> List[dict]:
        import httpx

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {
            "period1": period1,
            "period2": period2,
            "interval": interval,
            "includePrePost": "false",
        }
        headers = {
            "User-Agent": "Mozilla/5.0",
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params, headers=headers, timeout=15.0)

            if resp.status_code != 200:
                logger.warning("Yahoo Finance returned %d for %s", resp.status_code, symbol)
                return []

            data = resp.json()
            result = data.get("chart", {}).get("result", [])
            if not result:
                return []

            chart = result[0]
            timestamps = chart.get("timestamp", [])
            quote = chart.get("indicators", {}).get("quote", [{}])[0]

            opens = quote.get("open", [])
            highs = quote.get("high", [])
            lows = quote.get("low", [])
            closes = quote.get("close", [])
            volumes = quote.get("volume", [])

            candles: List[dict] = []
            for i, ts in enumerate(timestamps):
                if i >= len(opens) or opens[i] is None:
                    continue
                candles.append({
                    "time": ts,
                    "open": round(opens[i], 2),
                    "high": round(highs[i], 2) if highs[i] else round(opens[i], 2),
                    "low": round(lows[i], 2) if lows[i] else round(opens[i], 2),
                    "close": round(closes[i], 2) if closes[i] else round(opens[i], 2),
                    "volume": volumes[i] if i < len(volumes) and volumes[i] else 0,
                })

            logger.info("Fetched %d candles for %s from Yahoo Finance", len(candles), symbol)
            return candles

        except Exception:
            logger.exception("Yahoo Finance fetch failed for %s", symbol)
            return []

    def _generate_synthetic(
        self, center: datetime, hours_before: int, hours_after: int, interval: str
    ) -> List[dict]:
        """Generate synthetic candles when real data is unavailable."""
        import random
        random.seed(int(center.timestamp()))

        interval_minutes = {"1m": 1, "5m": 5, "15m": 15, "1h": 60}.get(interval, 5)
        start = center - timedelta(hours=hours_before)
        end = center + timedelta(hours=hours_after)

        price = 1000.0
        candles: List[dict] = []
        current = start

        while current < end:
            change = random.gauss(0, price * 0.001)
            o = price
            h = o + abs(random.gauss(0, price * 0.002))
            l = o - abs(random.gauss(0, price * 0.002))
            c = o + change
            price = c

            candles.append({
                "time": int(current.timestamp()),
                "open": round(o, 2),
                "high": round(max(o, h, c), 2),
                "low": round(min(o, l, c), 2),
                "close": round(c, 2),
                "volume": random.randint(1000, 50000),
            })
            current += timedelta(minutes=interval_minutes)

        return candles
