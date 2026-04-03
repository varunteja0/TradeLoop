"""
Broker Service — broker connection management and trade sync.

Handles: connect/disconnect, sync via OrderMatcher, trade persistence.
Emits: trade.synced
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crypto import encrypt_value, decrypt_value
from app.engine.broker_sync import OrderMatcher, normalize_zerodha_orders, normalize_angelone_orders
from app.models.broker_connection import BrokerConnection
from app.models.trade import Trade
from app.models.user import User
from app.services.event_bus import event_bus

logger = logging.getLogger("tradeloop.service.broker")

SUPPORTED_BROKERS = {"zerodha", "angelone"}


class BrokerService:

    async def connect(
        self, db: AsyncSession, user: User, broker: str, access_token: str, api_key: Optional[str] = None,
    ) -> Dict[str, str]:
        if broker not in SUPPORTED_BROKERS:
            raise ValueError(f"Supported brokers: {', '.join(SUPPORTED_BROKERS)}")

        existing = await db.execute(
            select(BrokerConnection).where(BrokerConnection.user_id == user.id, BrokerConnection.broker == broker)
        )
        for conn in existing.scalars().all():
            conn.is_active = False

        connection = BrokerConnection(
            user_id=user.id, broker=broker,
            access_token=encrypt_value(access_token),
            api_key=encrypt_value(api_key) if api_key else None,
        )
        db.add(connection)
        await db.flush()
        logger.info("Broker connected: %s for %s", broker, user.email)
        return {"status": "connected", "broker": broker, "connection_id": connection.id}

    async def list_connections(self, db: AsyncSession, user: User) -> List[Dict[str, Any]]:
        result = await db.execute(
            select(BrokerConnection).where(BrokerConnection.user_id == user.id)
            .order_by(BrokerConnection.created_at.desc())
        )
        return [
            {
                "id": c.id, "broker": c.broker, "is_active": c.is_active,
                "last_sync_at": c.last_sync_at.isoformat() if c.last_sync_at else None,
            }
            for c in result.scalars().all()
        ]

    async def get_connection(self, db: AsyncSession, user: User, connection_id: str) -> Optional[BrokerConnection]:
        result = await db.execute(
            select(BrokerConnection).where(
                BrokerConnection.id == connection_id, BrokerConnection.user_id == user.id,
            )
        )
        return result.scalar_one_or_none()

    async def sync_trades(self, db: AsyncSession, user: User, connection: BrokerConnection) -> Dict[str, Any]:
        if not connection.is_active:
            raise PermissionError("Connection is inactive. Please reconnect.")

        decrypted_token = decrypt_value(connection.access_token) if connection.access_token else ""
        decrypted_key = decrypt_value(connection.api_key) if connection.api_key else ""

        if not decrypted_token or decrypted_token == "test_token":
            broker_name = connection.broker.title()
            help_url = "console.zerodha.com" if connection.broker == "zerodha" else "smartapi.angelone.in"
            return {
                "status": "demo_mode", "broker": connection.broker,
                "message": f"Broker sync requires a valid {broker_name} API token. Get your API key from {help_url} and reconnect with real credentials.",
                "trades_synced": 0,
            }

        import httpx
        try:
            raw_orders = await self._fetch_orders(connection)
        except httpx.HTTPError as e:
            logger.error("Broker API error: %s", str(e))
            raise ConnectionError(f"Failed to reach {connection.broker.title()} API. Check your credentials.")

        matcher = OrderMatcher()
        matched = matcher.match_orders(raw_orders, source=connection.broker)

        synced = 0
        for t in matched:
            trade = Trade(
                user_id=user.id, symbol=t.symbol, side=t.side,
                entry_price=t.entry_price, exit_price=t.exit_price,
                quantity=t.quantity, pnl=t.pnl, timestamp=t.entry_time,
                duration_minutes=t.duration_minutes, fees=t.fees, source=t.source,
            )
            db.add(trade)
            synced += 1

        connection.last_sync_at = datetime.now(timezone.utc)
        await db.flush()

        await event_bus.emit("trade.synced", user_id=user.id, count=synced, broker=connection.broker)
        logger.info("Synced %d trades from %s for %s", synced, connection.broker, user.email)

        return {
            "status": "success", "broker": connection.broker,
            "message": f"Synced {synced} trades from {connection.broker.title()}.",
            "trades_synced": synced,
        }

    async def disconnect(self, db: AsyncSession, connection: BrokerConnection) -> None:
        connection.is_active = False
        await db.flush()

    async def _fetch_orders(self, connection: BrokerConnection) -> list:
        import httpx

        token = decrypt_value(connection.access_token) if connection.access_token else ""
        key = decrypt_value(connection.api_key) if connection.api_key else ""

        if connection.broker == "zerodha":
            headers = {"Authorization": f"token {key}:{token}"}
            async with httpx.AsyncClient() as client:
                resp = await client.get("https://api.kite.trade/orders", headers=headers, timeout=30.0)
            resp.raise_for_status()
            return normalize_zerodha_orders(resp.json().get("data", []))

        elif connection.broker == "angelone":
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-UserType": "USER", "X-SourceID": "WEB",
                "X-PrivateKey": key,
            }
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/getOrderBook",
                    headers=headers, timeout=30.0,
                )
            resp.raise_for_status()
            return normalize_angelone_orders(resp.json().get("data", []))

        raise ValueError(f"Unknown broker: {connection.broker}")
