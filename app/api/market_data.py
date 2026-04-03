from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.dependencies import get_current_user
from app.models.trade import Trade
from app.models.user import User
from app.services.market_data import MarketDataService

router = APIRouter(prefix="/market", tags=["market-data"])
market_service = MarketDataService()


@router.get("/ohlc/{symbol}")
async def get_ohlc(
    symbol: str,
    date: str = Query(..., description="Trade date ISO format YYYY-MM-DDTHH:MM:SS"),
    interval: str = Query("5m", description="Candle interval: 1m, 5m, 15m, 1h"),
    hours_before: int = Query(1),
    hours_after: int = Query(2),
    user: User = Depends(get_current_user),
):
    """Get historical OHLC data around a trade timestamp for replay."""
    try:
        trade_date = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    candles = await market_service.get_ohlc(
        symbol=symbol,
        trade_date=trade_date,
        interval=interval,
        hours_before=hours_before,
        hours_after=hours_after,
    )

    return {
        "symbol": symbol,
        "interval": interval,
        "candles": candles,
        "count": len(candles),
    }


@router.get("/replay/{trade_id}")
async def trade_replay(
    trade_id: str,
    interval: str = Query("5m"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get complete trade replay data: OHLC candles + trade markers + MFE/MAE."""
    result = await db.execute(
        select(Trade).where(Trade.id == trade_id, Trade.user_id == user.id)
    )
    trade = result.scalar_one_or_none()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    candles = await market_service.get_ohlc(
        symbol=trade.symbol,
        trade_date=trade.timestamp,
        interval=interval,
        hours_before=1,
        hours_after=3,
    )

    entry_time = int(trade.timestamp.timestamp())
    exit_time = entry_time + int((trade.duration_minutes or 30) * 60)

    mfe = 0.0
    mae = 0.0
    post_exit_max = 0.0

    for candle in candles:
        if candle["time"] >= entry_time and candle["time"] <= exit_time:
            if trade.side == "BUY":
                favorable = candle["high"] - trade.entry_price
                adverse = trade.entry_price - candle["low"]
            else:
                favorable = trade.entry_price - candle["low"]
                adverse = candle["high"] - trade.entry_price
            mfe = max(mfe, favorable)
            mae = max(mae, adverse)

        if candle["time"] > exit_time:
            if trade.side == "BUY":
                post_move = candle["high"] - trade.exit_price
            else:
                post_move = trade.exit_price - candle["low"]
            post_exit_max = max(post_exit_max, post_move)

    money_left = round(post_exit_max * trade.quantity, 2)

    return {
        "trade": {
            "id": trade.id,
            "symbol": trade.symbol,
            "side": trade.side,
            "entry_price": trade.entry_price,
            "exit_price": trade.exit_price,
            "entry_time": entry_time,
            "exit_time": exit_time,
            "pnl": trade.pnl,
            "quantity": trade.quantity,
        },
        "candles": candles,
        "mfe": {
            "price_move": round(mfe, 2),
            "dollar_value": round(mfe * trade.quantity, 2),
            "description": f"Price moved ${round(mfe, 2)} in your favor (max potential: ${round(mfe * trade.quantity, 2)})",
        },
        "mae": {
            "price_move": round(mae, 2),
            "dollar_value": round(mae * trade.quantity, 2),
            "description": f"Price moved ${round(mae, 2)} against you (max pain: ${round(mae * trade.quantity, 2)})",
        },
        "post_exit": {
            "max_move": round(post_exit_max, 2),
            "money_left_on_table": money_left,
            "description": (
                f"After you exited, price moved another ${round(post_exit_max, 2)} in your direction. "
                f"You left ${money_left} on the table."
            ) if money_left > 0 else "Price didn't move further in your direction after exit.",
        },
    }
