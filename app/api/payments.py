from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db
from app.dependencies import get_current_user
from app.models.user import User

logger = logging.getLogger("tradeloop.payments")

router = APIRouter(tags=["payments"])

PLAN_LIMITS = {
    "free": {"trades": 50, "features": ["basic_analytics", "csv_upload"]},
    "pro": {"trades": None, "price_inr": 99900, "features": ["basic_analytics", "csv_upload", "advanced_analytics", "behavior_alerts", "export", "broker_sync", "insights", "weekly_reports"]},
    "prop_trader": {"trades": None, "price_inr": 149900, "features": ["basic_analytics", "csv_upload", "advanced_analytics", "behavior_alerts", "export", "broker_sync", "insights", "weekly_reports", "prop_compliance", "multi_account", "real_time_alerts"]},
}

PAID_PLANS = {"pro", "prop_trader"}


class CreateOrderRequest(BaseModel):
    plan: str


class CreateOrderResponse(BaseModel):
    order_id: str
    amount: int
    currency: str
    key_id: str


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    plan: str


class VerifyPaymentResponse(BaseModel):
    verified: bool
    plan: str
    message: str


class PaymentStatusResponse(BaseModel):
    plan: str
    trade_limit: Optional[int]
    features: list[str]


@router.post("/payments/create-order", response_model=CreateOrderResponse)
async def create_order(
    body: CreateOrderRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    settings = get_settings()

    if body.plan not in PAID_PLANS:
        raise HTTPException(status_code=400, detail=f"Invalid plan. Must be one of: {', '.join(sorted(PAID_PLANS))}")

    if user.plan == body.plan:
        raise HTTPException(status_code=400, detail=f"You are already on the {body.plan} plan")

    plan_info = PLAN_LIMITS[body.plan]
    amount = plan_info["price_inr"]

    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        logger.warning("Razorpay keys not configured — returning mock order (dev mode)")
        return CreateOrderResponse(
            order_id="order_dev_mock_123",
            amount=amount,
            currency="INR",
            key_id="rzp_test_dev_mock",
        )

    import httpx

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.razorpay.com/v1/orders",
                auth=(settings.razorpay_key_id, settings.razorpay_key_secret),
                json={
                    "amount": amount,
                    "currency": "INR",
                    "receipt": f"tradeloop_{user.id}_{body.plan}",
                },
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as exc:
        logger.error("Razorpay order creation failed: %s", exc.response.text)
        raise HTTPException(status_code=502, detail="Payment gateway error")
    except httpx.RequestError as exc:
        logger.error("Razorpay request error: %s", exc)
        raise HTTPException(status_code=502, detail="Could not reach payment gateway")

    return CreateOrderResponse(
        order_id=data["id"],
        amount=data["amount"],
        currency=data["currency"],
        key_id=settings.razorpay_key_id,
    )


@router.post("/payments/verify", response_model=VerifyPaymentResponse)
async def verify_payment(
    body: VerifyPaymentRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    settings = get_settings()

    if body.plan not in PAID_PLANS:
        raise HTTPException(status_code=400, detail=f"Invalid plan. Must be one of: {', '.join(sorted(PAID_PLANS))}")

    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        logger.warning("Razorpay keys not configured — accepting payment in dev mode")
        user.plan = body.plan
        await db.commit()
        await db.refresh(user)
        return VerifyPaymentResponse(verified=True, plan=body.plan, message=f"Dev mode — upgraded to {body.plan}")

    expected_signature = hmac.new(
        settings.razorpay_key_secret.encode(),
        f"{body.razorpay_order_id}|{body.razorpay_payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, body.razorpay_signature):
        logger.warning("Invalid payment signature for user %s", user.id)
        raise HTTPException(status_code=400, detail="Payment verification failed")

    user.plan = body.plan
    await db.commit()
    await db.refresh(user)
    logger.info("User %s upgraded to %s (payment_id=%s)", user.id, body.plan, body.razorpay_payment_id)

    return VerifyPaymentResponse(verified=True, plan=body.plan, message=f"Payment verified — upgraded to {body.plan}")


@router.get("/payments/status", response_model=PaymentStatusResponse)
async def payment_status(user: User = Depends(get_current_user)):
    limits = PLAN_LIMITS.get(user.plan, PLAN_LIMITS["free"])
    return PaymentStatusResponse(
        plan=user.plan,
        trade_limit=limits["trades"],
        features=limits["features"],
    )
