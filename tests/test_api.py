from __future__ import annotations

import io

import pytest
import pytest_asyncio
from httpx import AsyncClient

from tests.conftest import SAMPLE_CSV

pytestmark = pytest.mark.asyncio


# =====================================================================
# Health check
# =====================================================================
class TestHealth:

    async def test_health_check(self, client: AsyncClient):
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "tradeloop"


# =====================================================================
# Registration
# =====================================================================
class TestRegistration:

    async def test_register_success(self, client: AsyncClient):
        resp = await client.post("/api/auth/register", json={
            "email": "new@tradeloop.dev",
            "password": "Secure1pass",
            "name": "New User",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["email"] == "new@tradeloop.dev"

    async def test_register_duplicate_email(self, client: AsyncClient):
        payload = {"email": "dup@tradeloop.dev", "password": "Secure1pass"}
        resp1 = await client.post("/api/auth/register", json=payload)
        assert resp1.status_code == 201

        resp2 = await client.post("/api/auth/register", json=payload)
        assert resp2.status_code == 409

    async def test_register_weak_password(self, client: AsyncClient):
        resp = await client.post("/api/auth/register", json={
            "email": "weak@tradeloop.dev",
            "password": "short",
        })
        assert resp.status_code == 422


# =====================================================================
# Login
# =====================================================================
class TestLogin:

    async def test_login_success(self, client: AsyncClient):
        await client.post("/api/auth/register", json={
            "email": "login@tradeloop.dev",
            "password": "Secure1pass",
        })
        resp = await client.post("/api/auth/login", json={
            "email": "login@tradeloop.dev",
            "password": "Secure1pass",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post("/api/auth/register", json={
            "email": "wrongpw@tradeloop.dev",
            "password": "Secure1pass",
        })
        resp = await client.post("/api/auth/login", json={
            "email": "wrongpw@tradeloop.dev",
            "password": "WrongPass1",
        })
        assert resp.status_code == 401


# =====================================================================
# CSV upload
# =====================================================================
class TestUpload:

    async def test_upload_csv(self, client: AsyncClient, auth_user: dict):
        resp = await client.post(
            "/api/trades/upload",
            headers=auth_user["headers"],
            files={"file": ("trades.csv", SAMPLE_CSV.encode(), "text/csv")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["imported"] == 3
        assert data["skipped"] == 0

    async def test_upload_too_large(self, client: AsyncClient, auth_user: dict):
        huge = "date,symbol,side,entry_price,exit_price,quantity,pnl\n" + "x" * (6 * 1024 * 1024)
        resp = await client.post(
            "/api/trades/upload",
            headers=auth_user["headers"],
            files={"file": ("big.csv", huge.encode(), "text/csv")},
        )
        assert resp.status_code in (400, 413)

    async def test_upload_wrong_format(self, client: AsyncClient, auth_user: dict):
        resp = await client.post(
            "/api/trades/upload",
            headers=auth_user["headers"],
            files={"file": ("data.txt", b"not csv data", "text/plain")},
        )
        assert resp.status_code == 400


# =====================================================================
# Trade CRUD
# =====================================================================
class TestTrades:

    async def _upload(self, client: AsyncClient, headers: dict) -> None:
        await client.post(
            "/api/trades/upload",
            headers=headers,
            files={"file": ("trades.csv", SAMPLE_CSV.encode(), "text/csv")},
        )

    async def test_get_trades(self, client: AsyncClient, auth_user: dict):
        await self._upload(client, auth_user["headers"])

        resp = await client.get("/api/trades", headers=auth_user["headers"])
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["trades"]) == 3

    async def test_delete_trade(self, client: AsyncClient, auth_user: dict):
        await self._upload(client, auth_user["headers"])

        list_resp = await client.get("/api/trades", headers=auth_user["headers"])
        trade_id = list_resp.json()["trades"][0]["id"]

        del_resp = await client.delete(f"/api/trades/{trade_id}", headers=auth_user["headers"])
        assert del_resp.status_code == 204

        list_resp2 = await client.get("/api/trades", headers=auth_user["headers"])
        assert list_resp2.json()["total"] == 2


# =====================================================================
# Analytics
# =====================================================================
class TestAnalytics:

    async def test_analytics_full(self, client: AsyncClient, auth_user: dict):
        await client.post(
            "/api/trades/upload",
            headers=auth_user["headers"],
            files={"file": ("trades.csv", SAMPLE_CSV.encode(), "text/csv")},
        )

        resp = await client.get("/api/analytics/full", headers=auth_user["headers"])
        assert resp.status_code == 200
        data = resp.json()
        for section in ("overview", "time_analysis", "behavioral", "symbols", "streaks", "equity_curve", "risk_metrics"):
            assert section in data


# =====================================================================
# Auth endpoints
# =====================================================================
class TestAuthEndpoints:

    async def test_auth_me(self, client: AsyncClient, auth_user: dict):
        resp = await client.get("/api/auth/me", headers=auth_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["email"] == "test@tradeloop.dev"

    async def test_unauthorized(self, client: AsyncClient):
        resp = await client.get("/api/trades")
        assert resp.status_code in (401, 403)

    async def test_change_password(self, client: AsyncClient):
        await client.post("/api/auth/register", json={
            "email": "chpw@tradeloop.dev",
            "password": "OldPass1secure",
        })
        login_resp = await client.post("/api/auth/login", json={
            "email": "chpw@tradeloop.dev",
            "password": "OldPass1secure",
        })
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        change_resp = await client.post("/api/auth/change-password", headers=headers, json={
            "current_password": "OldPass1secure",
            "new_password": "NewPass2secure",
        })
        assert change_resp.status_code == 204

        new_login = await client.post("/api/auth/login", json={
            "email": "chpw@tradeloop.dev",
            "password": "NewPass2secure",
        })
        assert new_login.status_code == 200

    async def test_update_profile(self, client: AsyncClient, auth_user: dict):
        resp = await client.put("/api/auth/profile", headers=auth_user["headers"], json={
            "name": "Updated Name",
            "timezone_offset": 5,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated Name"
        assert data["timezone_offset"] == 5
