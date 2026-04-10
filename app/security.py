from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

import bcrypt
import jwt

from app.config import get_settings

settings = get_settings()

MIN_PASSWORD_LENGTH = 8


def normalize_email(email: str) -> str:
    """Lowercase + strip for consistent login/register matching (emails are case-insensitive in practice)."""
    return email.strip().lower()


class TokenError(Exception):
    """Raised when token decode fails."""
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def validate_password(password: str) -> Tuple[bool, str]:
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    if not any(c.isalpha() for c in password):
        return False, "Password must contain at least one letter"
    return True, ""


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4()),
    })
    to_encode.setdefault("type", "access")
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "type": "refresh",
    })
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT. Raises TokenError with specific reason on failure."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except jwt.ExpiredSignatureError:
        raise TokenError("expired")
    except jwt.InvalidTokenError:
        raise TokenError("invalid")

    if payload.get("type") not in ("access", "reset", None):
        raise TokenError("wrong_token_type")

    return payload


def decode_refresh_token(token: str) -> dict:
    """Decode a refresh token. Raises TokenError on failure."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except jwt.ExpiredSignatureError:
        raise TokenError("expired")
    except jwt.InvalidTokenError:
        raise TokenError("invalid")

    if payload.get("type") != "refresh":
        raise TokenError("wrong_token_type")

    return payload
