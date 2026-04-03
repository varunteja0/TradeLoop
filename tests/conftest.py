from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from typing import AsyncGenerator, List

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.db import Base, get_db
from app.main import app


# ---------------------------------------------------------------------------
# Event loop
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# In-memory SQLite database for tests
# ---------------------------------------------------------------------------
TEST_DB_URL = "sqlite+aiosqlite://"

test_engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = _override_get_db


# ---------------------------------------------------------------------------
# Async HTTP test client
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# Authenticated user fixture — registers a user and returns headers + info
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def auth_user(client: AsyncClient) -> dict:
    resp = await client.post("/api/auth/register", json={
        "email": "test@tradeloop.dev",
        "password": "TestPass1",
        "name": "Test User",
    })
    assert resp.status_code == 201
    data = resp.json()
    return {
        "token": data["access_token"],
        "headers": {"Authorization": f"Bearer {data['access_token']}"},
        "user": data["user"],
    }


# ---------------------------------------------------------------------------
# Mock trade builder — returns SimpleNamespace objects that look like Trade
# ---------------------------------------------------------------------------
def make_trade(
    *,
    pnl: float,
    timestamp: datetime | None = None,
    symbol: str = "AAPL",
    side: str = "BUY",
    entry_price: float = 100.0,
    exit_price: float = 110.0,
    quantity: float = 10.0,
    duration_minutes: float | None = 30.0,
    setup_type: str | None = None,
    notes: str | None = None,
    fees: float = 1.0,
) -> SimpleNamespace:
    if timestamp is None:
        timestamp = datetime(2024, 6, 10, 14, 0, 0, tzinfo=timezone.utc)
    return SimpleNamespace(
        timestamp=timestamp,
        symbol=symbol,
        side=side,
        entry_price=entry_price,
        exit_price=exit_price,
        quantity=quantity,
        pnl=pnl,
        duration_minutes=duration_minutes,
        setup_type=setup_type,
        notes=notes,
        fees=fees,
    )


# ---------------------------------------------------------------------------
# Pre-built trade lists
# ---------------------------------------------------------------------------
BASE_TS = datetime(2024, 6, 10, 9, 0, 0, tzinfo=timezone.utc)  # Monday


@pytest.fixture
def ten_trades() -> List[SimpleNamespace]:
    """6 winners, 4 losers spread across hours."""
    return [
        make_trade(pnl=200, timestamp=BASE_TS + timedelta(hours=i), symbol="AAPL" if i % 2 == 0 else "TSLA")
        if i < 6 else
        make_trade(pnl=-150, timestamp=BASE_TS + timedelta(hours=i), symbol="MSFT")
        for i in range(10)
    ]


@pytest.fixture
def all_winners() -> List[SimpleNamespace]:
    return [make_trade(pnl=100 + i * 10, timestamp=BASE_TS + timedelta(hours=i)) for i in range(5)]


@pytest.fixture
def all_losers() -> List[SimpleNamespace]:
    return [make_trade(pnl=-(50 + i * 10), timestamp=BASE_TS + timedelta(hours=i)) for i in range(5)]


SAMPLE_CSV = (
    "date,symbol,side,entry_price,exit_price,quantity,pnl,duration,fees\n"
    "2024-06-10 09:00:00,AAPL,BUY,150.0,155.0,10,50.0,30,2.0\n"
    "2024-06-10 10:00:00,TSLA,SELL,200.0,195.0,5,25.0,45,1.5\n"
    "2024-06-10 11:00:00,MSFT,BUY,300.0,290.0,8,-80.0,20,3.0\n"
)
