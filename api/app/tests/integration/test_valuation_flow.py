"""Integration tests — wrapper valuation statement ingestion."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

PASSWORD = "S3cur3P@ss!"


async def _setup(client: AsyncClient) -> dict:
    await client.post("/api/v1/auth/setup", json={"password": PASSWORD})
    await client.post("/api/v1/auth/login", json={"password": PASSWORD})
    person = (await client.post(
        "/api/v1/persons", json={"name": "Antoine", "is_primary": True}
    )).json()
    return (await client.post("/api/v1/accounts", json={
        "name": "AV Vie Plus", "type": "investment_wrapper",
        "wrapper_type": "AV", "owner_id": person["id"],
    })).json()


async def test_save_valuation_creates_instruments_and_updates_networth(
    client: AsyncClient,
) -> None:
    acct = await _setup(client)

    res = await client.post("/api/v1/imports/pdf-valuation", json={
        "account_id": acct["id"],
        "as_of_date": "2025-12-31",
        "items": [
            {"label": "Fonds Euro Suravenir", "value": 12000.50},
            {"label": "Actions Monde ESG", "value": 8000.00},
        ],
    })
    assert res.status_code == 201
    body = res.json()
    assert body["saved"] == 2
    assert body["created_instruments"] == 2
    assert float(body["total_value"]) == 20000.50

    # Net worth reflects the statement values.
    nw = (await client.get("/api/v1/networth")).json()
    assert float(nw["current"]) == 20000.50

    # Valuations are NOT invested capital and must not feed XIRR cashflows.
    perf = (await client.get("/api/v1/portfolio/performance")).json()
    assert float(perf["total_invested"]) == 0.0
    assert float(perf["current_value"]) == 20000.50


async def test_resubmit_same_date_updates_in_place(client: AsyncClient) -> None:
    acct = await _setup(client)
    payload = {
        "account_id": acct["id"],
        "as_of_date": "2025-12-31",
        "items": [{"label": "Fonds Euro", "value": 1000.00}],
    }
    await client.post("/api/v1/imports/pdf-valuation", json=payload)

    # Corrected review, same statement date → update, not duplicate.
    payload["items"][0]["value"] = 1500.00
    res2 = await client.post("/api/v1/imports/pdf-valuation", json=payload)
    assert res2.json()["created_instruments"] == 0  # instrument reused by name

    nw = (await client.get("/api/v1/networth")).json()
    assert float(nw["current"]) == 1500.00


async def test_newer_statement_supersedes_older(client: AsyncClient) -> None:
    acct = await _setup(client)
    for as_of, value in (("2024-12-31", 1000.00), ("2025-12-31", 1200.00)):
        await client.post("/api/v1/imports/pdf-valuation", json={
            "account_id": acct["id"],
            "as_of_date": as_of,
            "items": [{"label": "Fonds Euro", "value": value}],
        })

    # Latest statement wins — values are never summed together.
    nw = (await client.get("/api/v1/networth")).json()
    assert float(nw["current"]) == 1200.00
