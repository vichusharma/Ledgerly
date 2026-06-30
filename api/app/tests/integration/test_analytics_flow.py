"""Integration tests — /transactions/analytics aggregation."""
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
        "name": "Compte courant", "type": "bank", "owner_id": person["id"],
    })).json()


async def _add(client: AsyncClient, acct_id: int, date: str, desc: str, amount: str) -> None:
    await client.post("/api/v1/transactions", json={
        "account_id": acct_id, "date": date, "description": desc, "amount": amount,
    })


async def test_analytics_aggregates(client: AsyncClient) -> None:
    acct = await _setup(client)
    aid = acct["id"]

    await _add(client, aid, "2026-05-03", "CB CARREFOUR MARKET 03/05 PARIS", "-40.00")
    await _add(client, aid, "2026-05-18", "CB CARREFOUR 18/05 LYON", "-60.00")
    await _add(client, aid, "2026-06-10", "PRLV TOTAL ENERGIE", "-90.00")
    await _add(client, aid, "2026-06-12", "VIR SALAIRE", "2000.00")

    res = await client.get("/api/v1/transactions/analytics")
    assert res.status_code == 200
    data = res.json()

    # Totals
    assert float(data["total_spent"]) == 190.00
    assert float(data["total_income"]) == 2000.00
    assert float(data["net"]) == 1810.00
    assert data["txn_count"] == 4

    # By month — two months present, May spent 100, June spent 90
    months = {m["month"]: m for m in data["by_month"]}
    assert float(months["2026-05"]["spent"]) == 100.00
    assert float(months["2026-06"]["spent"]) == 90.00
    assert float(months["2026-06"]["income"]) == 2000.00

    # Top merchants — Carrefour Market and Carrefour are separate merchants
    merchants = {m["merchant"]: m for m in data["top_merchants"]}
    carrefour_total = sum(
        float(v["spent"]) for k, v in merchants.items() if "Carrefour" in k
    )
    assert carrefour_total == 100.00

    # Date filter narrows to June only
    res2 = await client.get("/api/v1/transactions/analytics?from_date=2026-06-01")
    assert float(res2.json()["total_spent"]) == 90.00
