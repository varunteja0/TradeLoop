from __future__ import annotations

import logging
from datetime import timedelta

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.dependencies import get_current_user
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

logger = logging.getLogger("tradeloop.auth")
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
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

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserOut(id=str(user.id), email=user.email, name=user.name,
                     plan=user.plan, timezone_offset=user.timezone_offset),
    )


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.hashed_password):
        logger.warning("Failed login attempt for: %s", req.email)
        raise HTTPException(status_code=401, detail="Invalid email or password")

    logger.info("User logged in: %s", user.email)
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
    req: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not verify_password(req.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.hashed_password = hash_password(req.new_password)
    await db.flush()
    logger.info("Password changed: %s", user.email)


@router.post("/forgot-password")
async def forgot_password(email: EmailStr = Body(..., embed=True), db: AsyncSession = Depends(get_db)):
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
