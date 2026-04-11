"""Trading Rules API — CRUD for user rules + violation history."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.trading_rule import TradingRule
from app.models.rule_violation import RuleViolation

router = APIRouter(prefix="/rules", tags=["rules"])

VALID_RULE_TYPES = {
    "max_trades_per_day",
    "max_loss_per_day",
    "max_loss_per_trade",
    "no_trading_after",
    "no_trading_before",
    "max_consecutive_losses",
    "max_position_size",
}


class RuleCreateRequest(BaseModel):
    rule_type: str
    threshold: float
    label: Optional[str] = None


class RuleOut(BaseModel):
    id: str
    rule_type: str
    threshold: float
    is_active: bool
    label: Optional[str]

    model_config = {"from_attributes": True}


class ViolationOut(BaseModel):
    id: str
    rule_id: str
    trade_id: Optional[str]
    rule_type: str
    message: str
    severity: str
    created_at: str

    model_config = {"from_attributes": True}


@router.post("", response_model=RuleOut, status_code=status.HTTP_201_CREATED)
async def create_rule(
    req: RuleCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if req.rule_type not in VALID_RULE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid rule type. Must be one of: {', '.join(sorted(VALID_RULE_TYPES))}",
        )
    if req.threshold <= 0:
        raise HTTPException(status_code=400, detail="Threshold must be positive")

    rule = TradingRule(
        user_id=user.id,
        rule_type=req.rule_type,
        threshold=req.threshold,
        label=req.label,
    )
    db.add(rule)
    await db.flush()
    return rule


@router.get("", response_model=List[RuleOut])
async def list_rules(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(TradingRule)
        .where(TradingRule.user_id == user.id)
        .order_by(TradingRule.created_at.desc())
    )
    return result.scalars().all()


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(TradingRule).where(TradingRule.id == rule_id, TradingRule.user_id == user.id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    await db.delete(rule)


@router.patch("/{rule_id}")
async def toggle_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(TradingRule).where(TradingRule.id == rule_id, TradingRule.user_id == user.id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule.is_active = not rule.is_active
    await db.flush()
    return {"id": rule.id, "is_active": rule.is_active}


@router.get("/violations", response_model=List[ViolationOut])
async def list_violations(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(RuleViolation)
        .where(RuleViolation.user_id == user.id)
        .order_by(RuleViolation.created_at.desc())
        .limit(limit)
    )
    violations = result.scalars().all()
    return [
        ViolationOut(
            id=v.id,
            rule_id=v.rule_id,
            trade_id=v.trade_id,
            rule_type=v.rule_type,
            message=v.message,
            severity=v.severity,
            created_at=v.created_at.isoformat() if v.created_at else "",
        )
        for v in violations
    ]
