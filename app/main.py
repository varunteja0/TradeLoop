from __future__ import annotations

import logging
import os
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.db import engine, Base
from app.rate_limit import limiter
from app.api import auth, trades, analytics, payments, insights, prop_accounts, broker_connect, reports, market_data, admin

from app.logging_config import setup_logging
setup_logging()
logger = logging.getLogger("tradeloop")

settings = get_settings()
API_VERSION = "1"
APP_VERSION = "7.0.0"

sentry_dsn = getattr(settings, "sentry_dsn", "")
if sentry_dsn:
    import sentry_sdk
    sentry_sdk.init(
        dsn=sentry_dsn,
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        release=f"tradeloop@{APP_VERSION}",
        environment=settings.environment,
    )
    logger.info("Sentry initialized (release=%s)", APP_VERSION)


OPENAPI_TAGS = [
    {"name": "auth", "description": "Registration, login, token refresh, password management"},
    {"name": "trades", "description": "Trade CRUD, CSV upload/export, mood tagging"},
    {"name": "analytics", "description": "Full analytics, equity curve, risk metrics, emotions"},
    {"name": "insights", "description": "Counterfactual dollar-value analysis"},
    {"name": "prop-firm", "description": "Prop firm accounts and compliance tracking"},
    {"name": "broker-connect", "description": "Broker connection and trade sync"},
    {"name": "reports", "description": "Weekly intelligence reports"},
    {"name": "market-data", "description": "Historical OHLC and trade replay"},
    {"name": "payments", "description": "Subscription billing and plan management"},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("TradeLoop v%s starting up (env=%s)", APP_VERSION, settings.environment)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready")

    yield
    logger.info("TradeLoop shutting down")


app = FastAPI(
    title="TradeLoop",
    description="Trading behavior engine — the exact dollar cost of every mistake",
    version=APP_VERSION,
    lifespan=lifespan,
    openapi_tags=OPENAPI_TAGS,
    contact={"name": "TradeLoop Support", "email": "support@tradeloop.io"},
    license_info={"name": "Proprietary"},
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

origins = [settings.frontend_url]
if settings.environment == "development":
    origins.extend(["http://localhost:5173", "http://localhost:3000"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.middleware("http")
async def add_request_metadata(request: Request, call_next):
    request_id = uuid.uuid4().hex[:12]
    request.state.request_id = request_id
    response: Response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    response.headers["X-API-Version"] = API_VERSION
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.exception("Unhandled error [%s] %s %s", request_id, request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "detail": "Internal server error", "request_id": request_id},
    )


V1_PREFIX = "/api/v1"
COMPAT_PREFIX = "/api"

for prefix in (V1_PREFIX, COMPAT_PREFIX):
    app.include_router(auth.router, prefix=prefix)
    app.include_router(trades.router, prefix=prefix)
    app.include_router(analytics.router, prefix=prefix)
    app.include_router(payments.router, prefix=prefix)
    app.include_router(insights.router, prefix=prefix)
    app.include_router(prop_accounts.router, prefix=prefix)
    app.include_router(broker_connect.router, prefix=prefix)
    app.include_router(reports.router, prefix=prefix)
    app.include_router(market_data.router, prefix=prefix)
    app.include_router(admin.router, prefix=prefix)


@app.get("/api/health")
@app.get("/api/v1/health")
async def health(request: Request):
    from sqlalchemy import text as sa_text
    db_ok = False
    try:
        async with engine.connect() as conn:
            await conn.execute(sa_text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    return {
        "status": "ok" if db_ok else "degraded",
        "service": "tradeloop",
        "version": APP_VERSION,
        "api_version": API_VERSION,
        "database": "connected" if db_ok else "error",
        "request_id": getattr(request.state, "request_id", None),
    }
