from __future__ import annotations

import logging
import sys
from functools import lru_cache

from pydantic_settings import BaseSettings

logger = logging.getLogger("tradeloop")

_INSECURE_DEFAULT_KEY = "change-me-in-production-use-openssl-rand-hex-32"


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./tradeloop.db"
    secret_key: str = _INSECURE_DEFAULT_KEY
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    refresh_token_expire_days: int = 30
    frontend_url: str = "http://localhost:5173"
    environment: str = "development"
    free_tier_trade_limit: int = 50
    max_upload_size_bytes: int = 5 * 1024 * 1024  # 5MB
    rate_limit_login: str = "5/minute"
    rate_limit_register: str = "3/minute"
    rate_limit_upload: str = "10/minute"
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    pro_plan_price_paise: int = 99900  # ₹999

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.environment == "production" and settings.secret_key == _INSECURE_DEFAULT_KEY:
        logger.critical("FATAL: SECRET_KEY is the insecure default. Set a real key via env var.")
        sys.exit(1)
    return settings
