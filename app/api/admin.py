from __future__ import annotations
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.trade import Trade

logger = logging.getLogger("tradeloop.admin")
router = APIRouter(prefix="/admin", tags=["admin"])

async def require_admin(user: User = Depends(get_current_user)) -> User:
    if getattr(user, 'role', 'user') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

@router.get("/stats")
async def admin_stats(db: AsyncSession = Depends(get_db), user: User = Depends(require_admin)):
    total_users = await db.scalar(select(func.count()).select_from(User))
    paid_users = await db.scalar(select(func.count()).select_from(User).where(User.plan != "free"))
    total_trades = await db.scalar(select(func.count()).select_from(Trade))
    return {
        "total_users": total_users or 0,
        "paid_users": paid_users or 0,
        "total_trades": total_trades or 0,
        "plans": {
            "free": await db.scalar(select(func.count()).select_from(User).where(User.plan == "free")) or 0,
            "pro": await db.scalar(select(func.count()).select_from(User).where(User.plan == "pro")) or 0,
            "prop_trader": await db.scalar(select(func.count()).select_from(User).where(User.plan == "prop_trader")) or 0,
        },
    }
