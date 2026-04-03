from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db
from app.dependencies import get_current_user
from app.models.user import User

logger = logging.getLogger("tradeloop.payments")

router = APIRouter(tags=["payments"])

PLAN_LIMITS = {
    "free": {"trades": 50, "features": ["basic_analytics"]},
    "pro": {"trades": None, "features": ["basic_analytics", "advanced_analytics", "behavior_alerts", "export"]},
}


class CreateOrderResponse(BaseModel):
    order_id: str
    amount: int
    currency: str
    key_id: str


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


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
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    settings = get_settings()

    if user.plan == "pro":
        raise HTTPException(status_code=400, detail="You are already on the Pro plan")

    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        logger.warning("Razorpay keys not configured — returning mock order (dev mode)")
        return CreateOrderResponse(
            order_id="order_dev_mock_123",
            amount=settings.pro_plan_price_paise,
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
                    "amount": settings.pro_plan_price_paise,
                    "currency": "INR",
                    "receipt": f"tradeloop_{user.id}",
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

    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        logger.warning("Razorpay keys not configured — accepting payment in dev mode")
        user.plan = "pro"
        await db.commit()
        await db.refresh(user)
        return VerifyPaymentResponse(verified=True, plan="pro", message="Dev mode — payment accepted")

    expected_signature = hmac.new(
        settings.razorpay_key_secret.encode(),
        f"{body.razorpay_order_id}|{body.razorpay_payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, body.razorpay_signature):
        logger.warning("Invalid payment signature for user %s", user.id)
        raise HTTPException(status_code=400, detail="Payment verification failed")

    user.plan = "pro"
    await db.commit()
    await db.refresh(user)
    logger.info("User %s upgraded to pro (payment_id=%s)", user.id, body.razorpay_payment_id)

    return VerifyPaymentResponse(verified=True, plan="pro", message="Payment verified — upgraded to Pro")


@router.get("/payments/status", response_model=PaymentStatusResponse)
async def payment_status(user: User = Depends(get_current_user)):
    limits = PLAN_LIMITS.get(user.plan, PLAN_LIMITS["free"])
    return PaymentStatusResponse(
        plan=user.plan,
        trade_limit=limits["trades"],
        features=limits["features"],
    )
