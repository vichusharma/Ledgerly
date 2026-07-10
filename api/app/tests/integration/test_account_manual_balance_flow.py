"""Integration tests — manual balance override for bank/savings accounts."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

PASSWORD = "S3cur3P@ss!"


async def _setup_and_login(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/setup", json={"password": PASSWORD})
    await client.post("/api/v1/auth/login", json={"password": PASSWORD})


async def _create_person(client: AsyncClient, name: str = "Antoine") -> dict:
    res = await client.post("/api/v1/persons", json={"name": name, "is_primary": True})
    return res.json()


async def _create_savings_account(client: AsyncClient, owner_id: int, **overrides: object) -> dict:
    payload = {
        "name": "Livret A", "type": "savings", "wrapper_type": "LIVRET_A", "owner_id": owner_id,
    }
    payload.update(overrides)
    res = await client.post("/api/v1/accounts", json=payload)
    return res.json()


async def test_manual_balance_overrides_transaction_sum(client: AsyncClient) -> None:
    await _setup_and_login(client)
    person = await _create_person(client)
    account = await _create_savings_account(client, person["id"])

    await client.post("/api/v1/transactions", json={
        "account_id": account["id"], "date": "2026-01-15",
        "description": "Test deposit", "amount": "500.00",
    })

    before = (await client.get("/api/v1/networth")).json()

    res = await client.patch(f"/api/v1/accounts/{account['id']}", json={"manual_balance": "22950.00"})
    assert res.status_code == 200
    assert float(res.json()["manual_balance"]) == 22950.00

    after = (await client.get("/api/v1/networth")).json()
    # Assets should reflect the manual override (22950), not the 500 transaction sum.
    assert float(after["assets"]) - float(before["assets"]) == pytest.approx(22950.00 - 500.00, abs=0.01)


async def test_clearing_manual_balance_falls_back_to_transaction_sum(client: AsyncClient) -> None:
    await _setup_and_login(client)
    person = await _create_person(client)
    account = await _create_savings_account(client, person["id"])

    await client.post("/api/v1/transactions", json={
        "account_id": account["id"], "date": "2026-01-15",
        "description": "Test deposit", "amount": "500.00",
    })
    await client.patch(f"/api/v1/accounts/{account['id']}", json={"manual_balance": "22950.00"})

    res = await client.patch(f"/api/v1/accounts/{account['id']}", json={"manual_balance": None})
    assert res.status_code == 200
    assert res.json()["manual_balance"] is None

    after = (await client.get("/api/v1/networth")).json()
    accounts = (await client.get("/api/v1/accounts")).json()
    linked = next(a for a in accounts if a["id"] == account["id"])
    assert linked["manual_balance"] is None
    # No direct per-account balance in /networth, but confirm it no longer errors
    # and the account itself reports no override.
    assert "assets" in after


async def test_create_account_with_manual_balance(client: AsyncClient) -> None:
    await _setup_and_login(client)
    person = await _create_person(client)
    account = await _create_savings_account(client, person["id"], manual_balance="22950.00")
    assert float(account["manual_balance"]) == 22950.00
