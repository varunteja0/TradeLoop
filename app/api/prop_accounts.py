"""Prop Accounts API — thin routes, logic in ComplianceService."""
from __future__ import annotations

from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.compliance_service import ComplianceService

router = APIRouter(prefix="/prop", tags=["prop-firm"])
compliance_service = ComplianceService()


class PropAccountCreate(BaseModel):
    name: str
    firm: str
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
    return compliance_service.get_presets()


@router.post("", response_model=PropAccountOut, status_code=201)
async def create_prop_account(
    req: PropAccountCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    account = await compliance_service.create_account(
        db, user, name=req.name, firm=req.firm, phase=req.phase,
        initial_balance=req.initial_balance,
        overrides={k: v for k, v in req.model_dump().items() if k not in ("name", "firm", "phase", "initial_balance") and v is not None},
    )
    return account


@router.get("", response_model=List[PropAccountOut])
async def list_prop_accounts(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await compliance_service.list_accounts(db, user)


@router.get("/{account_id}/compliance")
async def check_compliance(
    account_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    account = await compliance_service.get_account(db, user, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Prop account not found")
    return await compliance_service.check_compliance(db, user, account)


@router.delete("/{account_id}", status_code=204)
async def delete_prop_account(
    account_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    try:
        await compliance_service.delete_account(db, user, account_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Prop account not found")
