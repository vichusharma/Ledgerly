"""Integration tests — net worth snapshot + series."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

PASSWORD = "S3cur3P@ss!"


async def _setup_and_login(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/setup", json={"password": PASSWORD})
    await client.post("/api/v1/auth/login", json={"password": PASSWORD})


async def test_networth_empty(client: AsyncClient) -> None:
    await _setup_and_login(client)
    res = await client.get("/api/v1/networth")
    assert res.status_code == 200
    data = res.json()
    assert "current" in data


async def test_manual_snapshot(client: AsyncClient) -> None:
    await _setup_and_login(client)
    res = await client.post("/api/v1/networth/snapshot")
    assert res.status_code in (200, 201, 204)


async def test_networth_series(client: AsyncClient) -> None:
    await _setup_and_login(client)
    await client.post("/api/v1/networth/snapshot")
    res = await client.get("/api/v1/networth/series")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


async def test_monte_carlo_endpoint(client: AsyncClient) -> None:
    await _setup_and_login(client)
    res = await client.post("/api/v1/scenarios/monte-carlo", json={
        "current_value": 50000.0,
        "monthly_contribution": 500.0,
        "annual_return_mu": 0.07,
        "annual_return_sigma": 0.12,
        "target_amount": 200000.0,
        "months_horizon": 120,
        "n_paths": 100,  # small for test speed
    })
    assert res.status_code == 200
    data = res.json()
    assert len(data["p10"]) == 120
    assert len(data["p50"]) == 120
    assert len(data["p90"]) == 120
    # p10 ≤ p50 ≤ p90 at every point
    for i in range(120):
        assert data["p10"][i] <= data["p50"][i]
        assert data["p50"][i] <= data["p90"][i]
