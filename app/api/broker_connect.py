"""Broker Connect API — thin routes, logic in BrokerService."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services import broker_svc as broker_service
from app.services.background import run_post_upload

router = APIRouter(prefix="/broker", tags=["broker-connect"])


class BrokerConnectRequest(BaseModel):
    broker: str
    access_token: str
    api_key: Optional[str] = None


@router.post("/connect")
async def connect_broker(
    req: BrokerConnectRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    try:
        return await broker_service.connect(db, user, req.broker, req.access_token, req.api_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/connections")
async def list_connections(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await broker_service.list_connections(db, user)


@router.post("/{connection_id}/sync")
async def sync_trades(
    connection_id: str,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    connection = await broker_service.get_connection(db, user, connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    try:
        result = await broker_service.sync_trades(db, user, connection)
    except PermissionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=502, detail=str(e))

    background_tasks.add_task(run_post_upload, user.id)
    return result


@router.delete("/{connection_id}")
async def disconnect_broker(
    connection_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    connection = await broker_service.get_connection(db, user, connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    await broker_service.disconnect(db, connection)
    return {"status": "disconnected"}
