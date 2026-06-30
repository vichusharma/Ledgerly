"""Integration tests — accounts + persons domain."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

PASSWORD = "S3cur3P@ss!"


async def _setup_and_login(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/setup", json={"password": PASSWORD})
    await client.post("/api/v1/auth/login", json={"password": PASSWORD})


async def test_create_person(client: AsyncClient) -> None:
    await _setup_and_login(client)
    res = await client.post("/api/v1/persons", json={"name": "Antoine", "is_primary": True})
    assert res.status_code == 201
    assert res.json()["name"] == "Antoine"


async def test_list_persons(client: AsyncClient) -> None:
    await _setup_and_login(client)
    await client.post("/api/v1/persons", json={"name": "Antoine", "is_primary": True})
    res = await client.get("/api/v1/persons")
    assert res.status_code == 200
    names = [p["name"] for p in res.json()]
    assert "Antoine" in names


async def test_create_account(client: AsyncClient) -> None:
    await _setup_and_login(client)
    person = (await client.post("/api/v1/persons", json={"name": "Antoine", "is_primary": True})).json()
    payload = {
        "name": "PEA Boursorama",
        "type": "investment_wrapper",
        "wrapper_type": "PEA",
        "institution": "Boursorama",
        "currency": "EUR",
        "owner_id": person["id"],
    }
    res = await client.post("/api/v1/accounts", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["wrapper_type"] == "PEA"
    assert data["institution"] == "Boursorama"


async def test_archive_account(client: AsyncClient) -> None:
    await _setup_and_login(client)
    person = (await client.post("/api/v1/persons", json={"name": "Antoine", "is_primary": True})).json()
    acct = (await client.post("/api/v1/accounts", json={
        "name": "Old savings", "type": "savings", "owner_id": person["id"],
    })).json()
    res = await client.delete(f"/api/v1/accounts/{acct['id']}/archive")
    assert res.status_code in (200, 204)
    # Archived accounts should not appear in the default list
    listing = await client.get("/api/v1/accounts")
    ids = [a["id"] for a in listing.json()]
    assert acct["id"] not in ids
