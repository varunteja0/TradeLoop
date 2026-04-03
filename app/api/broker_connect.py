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
    """Trigger a manual sync. In production, this would call the broker API.
    For now, returns the sync status."""
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

    logger.info("Sync triggered for %s (%s)", connection.broker, user.email)
    return {
        "status": "sync_initiated",
        "broker": connection.broker,
        "message": f"Sync with {connection.broker.title()} initiated. Trades will appear shortly.",
    }


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
