"""Integration tests — accounts + persons domain."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

PASSWORD = "S3cur3P@ss!"


async def _setup_and_login(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/setup", json={"password": PASSWORD})
    await client.post("/api/v1/auth/login", json={"password": PASSWORD})


async def test_price_lookup_setting_defaults_off_and_can_be_toggled(client: AsyncClient) -> None:
    await _setup_and_login(client)
    initial = (await client.get("/api/v1/settings/price-lookup")).json()
    assert initial["price_lookup_enabled"] is False

    enabled = (await client.put("/api/v1/settings/price-lookup", json={"price_lookup_enabled": True})).json()
    assert enabled["price_lookup_enabled"] is True

    persisted = (await client.get("/api/v1/settings/price-lookup")).json()
    assert persisted["price_lookup_enabled"] is True


async def test_create_person(client: AsyncClient) -> None:
    await _setup_and_login(client)
    res = await client.post("/api/v1/persons", json={"name": "Antoine", "is_primary": True})
    assert res.status_code == 201
    assert res.json()["name"] == "Antoine"


async def test_create_person_with_date_of_birth(client: AsyncClient) -> None:
    await _setup_and_login(client)
    res = await client.post("/api/v1/persons", json={
        "name": "Theo", "is_primary": False, "date_of_birth": "2015-06-01",
    })
    assert res.status_code == 201
    assert res.json()["date_of_birth"] == "2015-06-01"


async def test_update_person_date_of_birth(client: AsyncClient) -> None:
    await _setup_and_login(client)
    res = await client.post("/api/v1/persons", json={"name": "Theo", "is_primary": False})
    person = res.json()
    assert person["date_of_birth"] is None

    res = await client.patch(
        f"/api/v1/persons/{person['id']}", json={"date_of_birth": "2015-06-01"}
    )
    assert res.status_code == 200
    assert res.json()["date_of_birth"] == "2015-06-01"

    persisted = (await client.get("/api/v1/persons")).json()
    updated = next(p for p in persisted if p["id"] == person["id"])
    assert updated["date_of_birth"] == "2015-06-01"


async def test_update_unknown_person_404s(client: AsyncClient) -> None:
    await _setup_and_login(client)
    res = await client.patch("/api/v1/persons/99999", json={"date_of_birth": "2015-06-01"})
    assert res.status_code == 404


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
