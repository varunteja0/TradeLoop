from __future__ import annotations
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.dependencies import get_current_user
from app.models.prop_account import PropAccount
from app.models.trade import Trade
from app.models.user import User
from app.engine.prop_rules import PropComplianceEngine, FIRM_PRESETS

logger = logging.getLogger("tradeloop.prop")
router = APIRouter(prefix="/prop", tags=["prop-firm"])
compliance_engine = PropComplianceEngine()


class PropAccountCreate(BaseModel):
    name: str
    firm: str  # "ftmo", "fundingpips", etc. or "custom"
    phase: str = "challenge"
    initial_balance: float
    daily_loss_limit_pct: Optional[float] = None
    max_drawdown_pct: Optional[float] = None
    drawdown_type: Optional[str] = None
    profit_target_pct: Optional[float] = None
    min_trading_days: Optional[int] = None
    consistency_rule_pct: Optional[float] = None


class PropAccountOut(BaseModel):
    id: str
    name: str
    firm: str
    phase: str
    initial_balance: float
    daily_loss_limit_pct: float
    max_drawdown_pct: float
    drawdown_type: str
    profit_target_pct: Optional[float]
    min_trading_days: int
    consistency_rule_pct: Optional[float]
    is_active: bool
    status: str
    model_config = {"from_attributes": True}


@router.get("/presets")
async def get_presets():
    """Return available prop firm rule presets."""
    return FIRM_PRESETS


@router.post("", response_model=PropAccountOut, status_code=201)
async def create_prop_account(
    req: PropAccountCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    preset = FIRM_PRESETS.get(req.firm, {}).get(req.phase, {})

    account = PropAccount(
        user_id=user.id,
        name=req.name,
        firm=req.firm,
        phase=req.phase,
        initial_balance=req.initial_balance,
        daily_loss_limit_pct=req.daily_loss_limit_pct or preset.get("daily_loss_limit_pct", 5.0),
        max_drawdown_pct=req.max_drawdown_pct or preset.get("max_drawdown_pct", 10.0),
        drawdown_type=req.drawdown_type or preset.get("drawdown_type", "static"),
        profit_target_pct=req.profit_target_pct if req.profit_target_pct is not None else preset.get("profit_target_pct", 10.0),
        min_trading_days=req.min_trading_days or preset.get("min_trading_days", 10),
        consistency_rule_pct=req.consistency_rule_pct if req.consistency_rule_pct is not None else preset.get("consistency_rule_pct"),
    )
    db.add(account)
    await db.flush()
    logger.info("Prop account created: %s for %s", account.name, user.email)
    return account


@router.get("", response_model=List[PropAccountOut])
async def list_prop_accounts(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PropAccount).where(PropAccount.user_id == user.id).order_by(PropAccount.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{account_id}/compliance")
async def check_compliance(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PropAccount).where(PropAccount.id == account_id, PropAccount.user_id == user.id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Prop account not found")

    trades_result = await db.execute(
        select(Trade).where(Trade.user_id == user.id).order_by(Trade.timestamp)
    )
    trades = list(trades_result.scalars().all())

    config = {
        "initial_balance": account.initial_balance,
        "daily_loss_limit_pct": account.daily_loss_limit_pct,
        "max_drawdown_pct": account.max_drawdown_pct,
        "drawdown_type": account.drawdown_type,
        "profit_target_pct": account.profit_target_pct,
        "min_trading_days": account.min_trading_days,
        "consistency_rule_pct": account.consistency_rule_pct,
    }

    report = compliance_engine.check_compliance(trades, config)
    return report


@router.delete("/{account_id}", status_code=204)
async def delete_prop_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PropAccount).where(PropAccount.id == account_id, PropAccount.user_id == user.id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Prop account not found")
    await db.delete(account)
