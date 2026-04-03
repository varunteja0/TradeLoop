from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.dependencies import get_current_user
from app.rate_limit import limiter
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest, LoginRequest, AuthResponse, UserOut,
    ChangePasswordRequest, UpdateProfileRequest, RefreshRequest,
)
from app.security import (
    hash_password, verify_password, validate_password,
    create_access_token, create_refresh_token,
    decode_access_token, decode_refresh_token, TokenError,
)
from app.services.audit_service import audit_service
from app.models.audit_log import AuditLog

logger = logging.getLogger("tradeloop.auth")
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def register(request: Request, req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        name=req.name,
    )
    db.add(user)
    await db.flush()

    logger.info("User registered: %s", user.email)
    await audit_service.log(db, user.id, "register", ip=request.client.host)

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserOut(id=str(user.id), email=user.email, name=user.name,
                     plan=user.plan, timezone_offset=user.timezone_offset),
    )


@router.post("/login", response_model=AuthResponse)
@limiter.limit("5/minute")
async def login(request: Request, req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()

    if user and user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise HTTPException(status_code=429, detail="Account temporarily locked. Try again in 15 minutes.")

    if not user or not verify_password(req.password, user.hashed_password):
        if user:
            user.failed_login_count = (user.failed_login_count or 0) + 1
            if user.failed_login_count >= 5:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
            await db.flush()
        logger.warning("Failed login attempt for: %s", req.email)
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user.failed_login_count = 0
    user.locked_until = None

    logger.info("User logged in: %s", user.email)
    await audit_service.log(db, user.id, "login", ip=request.client.host)
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserOut(id=str(user.id), email=user.email, name=user.name,
                     plan=user.plan, timezone_offset=user.timezone_offset),
    )


@router.post("/refresh", response_model=AuthResponse)
async def refresh(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_refresh_token(req.refresh_token)
    except TokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid refresh token: {e.reason}")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserOut(id=str(user.id), email=user.email, name=user.name,
                     plan=user.plan, timezone_offset=user.timezone_offset),
    )


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return UserOut(id=str(user.id), email=user.email, name=user.name,
                   plan=user.plan, timezone_offset=user.timezone_offset)


@router.put("/profile", response_model=UserOut)
async def update_profile(
    req: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if req.name is not None:
        user.name = req.name
    if req.timezone_offset is not None:
        user.timezone_offset = req.timezone_offset
    await db.flush()
    logger.info("Profile updated: %s", user.email)
    return UserOut(id=str(user.id), email=user.email, name=user.name,
                   plan=user.plan, timezone_offset=user.timezone_offset)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    request: Request,
    req: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not verify_password(req.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.hashed_password = hash_password(req.new_password)
    await db.flush()
    logger.info("Password changed: %s", user.email)
    await audit_service.log(db, user.id, "password_change", ip=request.client.host)


@router.post("/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(request: Request, email: EmailStr = Body(..., embed=True), db: AsyncSession = Depends(get_db)):
    """Send password reset email."""
    from app.services.email_service import EmailService
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        return {"message": "If that email is registered, a reset link has been sent."}

    reset_token = create_access_token({"sub": str(user.id), "type": "reset"}, expires_delta=timedelta(hours=1))
    email_svc = EmailService()
    await email_svc.send_password_reset(user.email, reset_token)
    return {"message": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(token: str = Body(...), new_password: str = Body(...), db: AsyncSession = Depends(get_db)):
    """Reset password with token from email."""
    valid, msg = validate_password(new_password)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)

    try:
        payload = decode_access_token(token)
    except TokenError:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    if payload.get("type") != "reset":
        raise HTTPException(status_code=400, detail="Invalid token type")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")

    user.hashed_password = hash_password(new_password)
    await db.flush()
    return {"message": "Password reset successfully"}


@router.get("/audit-log")
async def audit_log(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.user_id == user.id)
        .order_by(AuditLog.created_at.desc())
        .limit(50)
    )
    entries = result.scalars().all()
    return [
        {
            "id": e.id,
            "action": e.action,
            "details": e.details,
            "ip_address": e.ip_address,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in entries
    ]
