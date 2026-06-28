"""Integration tests — auth flow: setup, login, session, logout."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_setup_creates_household(client: AsyncClient) -> None:
    """POST /auth/setup should create household and return 201."""
    res = await client.post("/api/v1/auth/setup", json={"password": "S3cur3P@ss!"})
    assert res.status_code == 201, res.text


async def test_login_sets_cookie(client: AsyncClient) -> None:
    """POST /auth/login with correct password should set httpOnly cookie."""
    # Ensure household exists
    await client.post("/api/v1/auth/setup", json={"password": "S3cur3P@ss!"})
    res = await client.post("/api/v1/auth/login", json={"password": "S3cur3P@ss!"})
    assert res.status_code == 200
    assert "access_token" in res.cookies


async def test_session_returns_ok(client: AsyncClient) -> None:
    """GET /auth/session after login should return 200."""
    await client.post("/api/v1/auth/setup", json={"password": "S3cur3P@ss!"})
    await client.post("/api/v1/auth/login", json={"password": "S3cur3P@ss!"})
    res = await client.get("/api/v1/auth/session")
    assert res.status_code == 200


async def test_wrong_password_rejected(client: AsyncClient) -> None:
    """POST /auth/login with wrong password should return 401."""
    await client.post("/api/v1/auth/setup", json={"password": "S3cur3P@ss!"})
    res = await client.post("/api/v1/auth/login", json={"password": "wrongpassword"})
    assert res.status_code == 401


async def test_logout_clears_session(client: AsyncClient) -> None:
    """POST /auth/logout then GET /auth/session should return 401."""
    await client.post("/api/v1/auth/setup", json={"password": "S3cur3P@ss!"})
    await client.post("/api/v1/auth/login", json={"password": "S3cur3P@ss!"})
    logout = await client.post("/api/v1/auth/logout")
    assert logout.status_code == 200
    session = await client.get("/api/v1/auth/session")
    assert session.status_code == 401
