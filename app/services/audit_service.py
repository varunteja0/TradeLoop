from __future__ import annotations
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog

logger = logging.getLogger("tradeloop.audit")

class AuditService:
    async def log(self, db: AsyncSession, user_id: str, action: str, details: Optional[str] = None, ip: Optional[str] = None) -> None:
        entry = AuditLog(user_id=user_id, action=action, details=details, ip_address=ip)
        db.add(entry)
        await db.flush()
        logger.info("Audit: user=%s action=%s", user_id, action)

audit_service = AuditService()
