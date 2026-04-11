"""
Trade Service — all trade business logic in one place.

Handles: CSV upload + parsing, free tier enforcement, trade CRUD, export.
Emits events: trade.uploaded, trade.deleted
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, cast

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.engine.csv_parser import parse_csv, BrokerFormat
from app.models.trade import Trade
from app.models.user import User
from app.services.event_bus import event_bus

logger = logging.getLogger("tradeloop.service.trade")
settings = get_settings()

VALID_BROKERS = {"auto", "generic", "zerodha", "mt4"}


@dataclass
class UploadResult:
    imported: int
    skipped: int
    errors: List[str]


@dataclass
class TradeListResult:
    trades: list
    total: int
    page: int
    per_page: int


class TradeService:

    async def upload_csv(
        self, db: AsyncSession, user: User, content: str, broker: str = "auto"
    ) -> UploadResult:
        """Parse CSV content, enforce limits, persist trades, emit event."""
        if broker not in VALID_BROKERS:
            raise ValueError(f"Invalid broker. Must be one of: {', '.join(VALID_BROKERS)}")

        parsed, parse_errors = parse_csv(content, broker=cast(BrokerFormat, broker))
        if not parsed:
            detail = "No valid trades found in the CSV."
            if parse_errors:
                detail += " Errors: " + "; ".join(parse_errors)
            raise ValueError(detail)

        imported = 0
        skipped = 0
        errors = list(parse_errors)

        for trade_data in parsed:
            try:
                trade = Trade(
                    user_id=user.id,
                    timestamp=trade_data.timestamp,
                    symbol=trade_data.symbol,
                    side=trade_data.side,
                    entry_price=trade_data.entry_price,
                    exit_price=trade_data.exit_price,
                    quantity=trade_data.quantity,
                    pnl=trade_data.pnl,
                    duration_minutes=trade_data.duration_minutes,
                    setup_type=trade_data.setup_type,
                    notes=trade_data.notes,
                    fees=trade_data.fees,
                    source="csv",
                )
                db.add(trade)
                imported += 1
            except Exception as e:
                skipped += 1
                errors.append(str(e))

        await db.flush()
        logger.info("User %s uploaded %d trades (skipped: %d)", user.email, imported, skipped)

        if imported > 0:
            await event_bus.emit("trade.uploaded", user_id=user.id, count=imported)

        return UploadResult(imported=imported, skipped=skipped, errors=errors)

    async def list_trades(
        self,
        db: AsyncSession,
        user: User,
        page: int = 1,
        per_page: int = 50,
        symbol: Optional[str] = None,
        side: Optional[str] = None,
        sort_by: str = "timestamp",
        sort_dir: str = "desc",
        search: Optional[str] = None,
    ) -> TradeListResult:
        """List trades with filtering, sorting, pagination."""
        query = select(Trade).where(Trade.user_id == user.id)
        count_query = select(func.count()).select_from(Trade).where(Trade.user_id == user.id)

        if symbol:
            query = query.where(Trade.symbol == symbol.upper())
            count_query = count_query.where(Trade.symbol == symbol.upper())
        if side and side.upper() in ("BUY", "SELL"):
            query = query.where(Trade.side == side.upper())
            count_query = count_query.where(Trade.side == side.upper())
        if search:
            query = query.where(Trade.symbol.contains(search.upper()))
            count_query = count_query.where(Trade.symbol.contains(search.upper()))

        sort_col_map = {"timestamp": Trade.timestamp, "pnl": Trade.pnl, "symbol": Trade.symbol}
        sort_col = sort_col_map.get(sort_by, Trade.timestamp)
        order = sort_col.desc() if sort_dir == "desc" else sort_col.asc()

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(order).offset((page - 1) * per_page).limit(per_page)
        result = await db.execute(query)
        trades = list(result.scalars().all())

        return TradeListResult(trades=trades, total=total, page=page, per_page=per_page)

    async def get_user_trades(self, db: AsyncSession, user: User, limit: Optional[int] = None) -> list:
        """Get all trades for a user, ordered by timestamp."""
        query = select(Trade).where(Trade.user_id == user.id).order_by(Trade.timestamp)
        if limit is not None:
            query = query.limit(limit)
        result = await db.execute(query)
        trades = list(result.scalars().all())
        if limit is not None and len(trades) == limit:
            logger.warning("User %s hit trade fetch limit of %d — results may be truncated", user.email, limit)
        return trades

    async def delete_trade(self, db: AsyncSession, user: User, trade_id: str) -> None:
        result = await db.execute(
            select(Trade).where(Trade.id == trade_id, Trade.user_id == user.id)
        )
        trade = result.scalar_one_or_none()
        if not trade:
            raise LookupError("Trade not found")
        await db.delete(trade)
        await event_bus.emit("trade.deleted", user_id=user.id, trade_id=trade_id)
        logger.info("Trade %s deleted by user %s", trade_id, user.email)

    async def delete_all_trades(self, db: AsyncSession, user: User) -> None:
        await db.execute(delete(Trade).where(Trade.user_id == user.id))
        await event_bus.emit("trade.deleted", user_id=user.id, trade_id="all")
        logger.warning("All trades deleted for user %s", user.email)

    async def export_csv(self, db: AsyncSession, user: User) -> str:
        """Export all trades as CSV string."""
        result = await db.execute(
            select(Trade).where(Trade.user_id == user.id).order_by(Trade.timestamp)
        )
        trades = result.scalars().all()
        lines = ["date,symbol,side,entry_price,exit_price,quantity,pnl,duration,setup,notes,fees,mood,reason,rule_followed,mistake_category"]
        for t in trades:
            lines.append(
                f"{t.timestamp.isoformat()},{t.symbol},{t.side},{t.entry_price},"
                f"{t.exit_price},{t.quantity},{t.pnl},{t.duration_minutes or ''},"
                f"{t.setup_type or ''},{(t.notes or '').replace(',', ';')},{t.fees},"
                f"{t.mood or ''},{(t.reason or '').replace(',', ';')},"
                f"{'' if t.rule_followed is None else t.rule_followed},{t.mistake_category or ''}"
            )
        return "\n".join(lines)

    async def update_trade(self, db: AsyncSession, user: User, trade_id: str, updates: dict) -> None:
        result = await db.execute(select(Trade).where(Trade.id == trade_id, Trade.user_id == user.id))
        trade = result.scalar_one_or_none()
        if not trade:
            raise LookupError("Trade not found")
        allowed = {"mood", "notes", "setup_type", "reason", "rule_followed", "mistake_category"}
        for key, value in updates.items():
            if key in allowed:
                setattr(trade, key, value)
        await db.flush()

    async def list_symbols(self, db: AsyncSession, user: User) -> List[Dict]:
        result = await db.execute(
            select(Trade.symbol, func.count()).where(Trade.user_id == user.id)
            .group_by(Trade.symbol).order_by(func.count().desc())
        )
        return [{"symbol": row[0], "count": row[1]} for row in result.all()]

    async def _check_free_tier(self, db: AsyncSession, user: User) -> Optional[int]:
        """Returns remaining trade slots, or None for unlimited (all plans now unlimited)."""
        return None
