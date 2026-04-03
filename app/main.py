from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.db import engine, Base
from app.api import auth, trades, analytics, payments, insights, prop_accounts, broker_connect, reports

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("tradeloop")

settings = get_settings()

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("TradeLoop starting up (env=%s)", settings.environment)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready")
    yield
    logger.info("TradeLoop shutting down")


app = FastAPI(
    title="TradeLoop",
    description="Trade journal analytics engine for day traders and prop firm traders",
    version="3.0.0",
    lifespan=lifespan,
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


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.include_router(auth.router, prefix="/api")
app.include_router(trades.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(payments.router, prefix="/api")
app.include_router(insights.router, prefix="/api")
app.include_router(prop_accounts.router, prefix="/api")
app.include_router(broker_connect.router, prefix="/api")
app.include_router(reports.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "tradeloop", "version": "3.0.0"}
