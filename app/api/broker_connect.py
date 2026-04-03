from __future__ import annotations
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.dependencies import get_current_user
from app.models.broker_connection import BrokerConnection
from app.models.trade import Trade
from app.models.user import User

logger = logging.getLogger("tradeloop.broker")
router = APIRouter(prefix="/broker", tags=["broker-connect"])


class BrokerConnectRequest(BaseModel):
    broker: str  # "zerodha" or "angelone"
    access_token: str
    api_key: Optional[str] = None


class BrokerConnectionOut(BaseModel):
    id: str
    broker: str
    is_active: bool
    last_sync_at: Optional[str]
    created_at: str
    model_config = {"from_attributes": True}


@router.post("/connect")
async def connect_broker(
    req: BrokerConnectRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if req.broker not in ("zerodha", "angelone"):
        raise HTTPException(status_code=400, detail="Supported brokers: zerodha, angelone")

    existing = await db.execute(
        select(BrokerConnection).where(
            BrokerConnection.user_id == user.id,
            BrokerConnection.broker == req.broker,
        )
    )
    for conn in existing.scalars().all():
        conn.is_active = False

    connection = BrokerConnection(
        user_id=user.id,
        broker=req.broker,
        access_token=req.access_token,
        api_key=req.api_key,
    )
    db.add(connection)
    await db.flush()

    logger.info("Broker connected: %s for %s", req.broker, user.email)
    return {"status": "connected", "broker": req.broker, "connection_id": connection.id}


@router.get("/connections")
async def list_connections(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(BrokerConnection).where(BrokerConnection.user_id == user.id).order_by(BrokerConnection.created_at.desc())
    )
    connections = result.scalars().all()
    return [
        {
            "id": c.id,
            "broker": c.broker,
            "is_active": c.is_active,
            "last_sync_at": c.last_sync_at.isoformat() if c.last_sync_at else None,
        }
        for c in connections
    ]


@router.post("/{connection_id}/sync")
async def sync_trades(
    connection_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Sync trades from broker. Calls broker API, matches orders, persists trades."""
    from datetime import datetime, timezone
    from app.engine.broker_sync import OrderMatcher, normalize_zerodha_orders, normalize_angelone_orders

    result = await db.execute(
        select(BrokerConnection).where(
            BrokerConnection.id == connection_id,
            BrokerConnection.user_id == user.id,
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    if not connection.is_active:
        raise HTTPException(status_code=400, detail="Connection is inactive. Please reconnect.")

    if not connection.access_token or connection.access_token == "test_token":
        return {
            "status": "demo_mode",
            "broker": connection.broker,
            "message": (
                f"Broker sync requires a valid {connection.broker.title()} API token. "
                f"Get your API key from {'console.zerodha.com' if connection.broker == 'zerodha' else 'smartapi.angelone.in'} "
                f"and reconnect with real credentials. Using CSV upload in the meantime."
            ),
            "trades_synced": 0,
        }

    try:
        import httpx

        if connection.broker == "zerodha":
            headers = {"Authorization": f"token {connection.api_key}:{connection.access_token}"}
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://api.kite.trade/orders",
                    headers=headers,
                    timeout=30.0,
                )
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail=f"Zerodha API error: {resp.status_code}")
            raw_orders = normalize_zerodha_orders(resp.json().get("data", []))

        elif connection.broker == "angelone":
            headers = {
                "Authorization": f"Bearer {connection.access_token}",
                "Content-Type": "application/json",
                "X-ClientLocalIP": "127.0.0.1",
                "X-MACAddress": "00:00:00:00:00:00",
                "X-UserType": "USER",
                "X-SourceID": "WEB",
                "X-PrivateKey": connection.api_key or "",
            }
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://apiconnect.angelone.in/rest/secure/angelbroking/order/v1/getOrderBook",
                    headers=headers,
                    timeout=30.0,
                )
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail=f"Angel One API error: {resp.status_code}")
            raw_orders = normalize_angelone_orders(resp.json().get("data", []))
        else:
            raise HTTPException(status_code=400, detail=f"Unknown broker: {connection.broker}")

        matcher = OrderMatcher()
        matched_trades = matcher.match_orders(raw_orders, source=connection.broker)

        synced = 0
        for t in matched_trades:
            trade = Trade(
                user_id=user.id,
                symbol=t.symbol,
                side=t.side,
                entry_price=t.entry_price,
                exit_price=t.exit_price,
                quantity=t.quantity,
                pnl=t.pnl,
                timestamp=t.entry_time,
                duration_minutes=t.duration_minutes,
                fees=t.fees,
                source=t.source,
            )
            db.add(trade)
            synced += 1

        connection.last_sync_at = datetime.now(timezone.utc)
        await db.flush()

        logger.info("Synced %d trades from %s for %s", synced, connection.broker, user.email)
        return {
            "status": "success",
            "broker": connection.broker,
            "message": f"Synced {synced} trades from {connection.broker.title()}.",
            "trades_synced": synced,
        }

    except httpx.HTTPError as e:
        logger.error("Broker API error: %s", str(e))
        raise HTTPException(status_code=502, detail=f"Failed to reach {connection.broker.title()} API. Check your credentials.")


@router.delete("/{connection_id}")
async def disconnect_broker(
    connection_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(BrokerConnection).where(
            BrokerConnection.id == connection_id,
            BrokerConnection.user_id == user.id,
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    connection.is_active = False
    await db.flush()
    return {"status": "disconnected"}
