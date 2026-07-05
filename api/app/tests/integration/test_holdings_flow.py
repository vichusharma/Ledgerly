"""Integration tests — add-holding-by-ISIN and aggregated holdings view."""
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
        "name": "CTO Boursorama", "type": "investment_wrapper",
        "wrapper_type": "CTO", "owner_id": person["id"],
    })).json()


async def test_add_holding_creates_instrument_lot_price_and_shows_in_holdings(
    client: AsyncClient,
) -> None:
    acct = await _setup(client)

    res = await client.post("/api/v1/portfolio/holdings", json={
        "isin": "IE00B4L5Y983",
        "quantity": 10,
        "account_id": acct["id"],
        "price": 98.32,
        "name": "iShares Core MSCI World",
        "ticker": "IWDA",
        "currency": "EUR",
    })
    assert res.status_code == 201
    body = res.json()
    assert body["instrument"]["isin"] == "IE00B4L5Y983"
    assert body["lot"]["lot_type"] == "buy"

    holdings = (await client.get("/api/v1/portfolio/holdings")).json()
    assert float(holdings["total_value"]) == pytest.approx(983.2)
    assert len(holdings["rows"]) == 1
    row = holdings["rows"][0]
    assert row["isin"] == "IE00B4L5Y983"
    assert float(row["quantity"]) == 10
    assert float(row["market_value"]) == pytest.approx(983.2)
    assert row["owner_name"] == "Antoine"
    assert row["account_name"] == "CTO Boursorama"


async def test_add_same_isin_twice_reuses_instrument_and_sums_quantity(
    client: AsyncClient,
) -> None:
    acct = await _setup(client)
    payload = {
        "isin": "IE00B4L5Y983", "quantity": 5, "account_id": acct["id"],
        "price": 100.0, "name": "iShares Core MSCI World",
    }
    r1 = await client.post("/api/v1/portfolio/holdings", json=payload)
    payload["quantity"] = 3
    payload["price"] = 102.0
    r2 = await client.post("/api/v1/portfolio/holdings", json=payload)

    assert r1.json()["instrument"]["id"] == r2.json()["instrument"]["id"]

    instruments = (await client.get("/api/v1/instruments")).json()
    assert len(instruments) == 1

    holdings = (await client.get("/api/v1/portfolio/holdings")).json()
    assert len(holdings["rows"]) == 1
    assert float(holdings["rows"][0]["quantity"]) == 8

    lots = (await client.get("/api/v1/investment-lots")).json()
    assert len(lots) == 2


async def test_instrument_lookup_is_disabled_by_default(client: AsyncClient) -> None:
    await _setup(client)
    res = await client.get("/api/v1/instruments/lookup", params={"isin": "IE00B4L5Y983"})
    assert res.status_code == 404


async def test_performance_and_allocation_unaffected_by_positions_refactor(
    client: AsyncClient,
) -> None:
    acct = await _setup(client)
    await client.post("/api/v1/portfolio/holdings", json={
        "isin": "IE00B4L5Y983", "quantity": 10, "account_id": acct["id"],
        "price": 100.0, "name": "iShares Core MSCI World", "asset_class": "equity",
    })

    perf = (await client.get("/api/v1/portfolio/performance")).json()
    assert float(perf["current_value"]) == pytest.approx(1000.0)
    assert float(perf["total_invested"]) == pytest.approx(1000.0)

    alloc = (await client.get("/api/v1/portfolio/allocation")).json()
    assert float(alloc["total_value"]) == pytest.approx(1000.0)
    equity_slice = next(s for s in alloc["by_class"] if s["asset_class"] == "equity")
    assert float(equity_slice["market_value"]) == pytest.approx(1000.0)
