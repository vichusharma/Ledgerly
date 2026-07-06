"""Integration tests — per-person impatriate profile + household filing
status/dependents (Feature I2, facts only, no tax computation yet)."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

PASSWORD = "S3cur3P@ss!"


async def _person(client: AsyncClient, name: str = "Antoine") -> dict:
    await client.post("/api/v1/auth/setup", json={"password": PASSWORD})
    await client.post("/api/v1/auth/login", json={"password": PASSWORD})
    return (await client.post(
        "/api/v1/persons", json={"name": name, "is_primary": True}
    )).json()


async def test_get_person_tax_profile_defaults_off(client: AsyncClient) -> None:
    person = await _person(client)

    res = await client.get(f"/api/v1/tax/profile/{person['id']}")
    assert res.status_code == 200
    body = res.json()
    assert body["person_id"] == person["id"]
    assert body["impatriate_enabled"] is False
    assert body["impatriate_arrival_date"] is None
    assert body["impatriate_election_method"] is None


async def test_get_tax_profile_missing_person_404s(client: AsyncClient) -> None:
    await _person(client)
    res = await client.get("/api/v1/tax/profile/999999")
    assert res.status_code == 404


async def test_set_person_tax_profile_enables_impatriate_regime(client: AsyncClient) -> None:
    person = await _person(client)

    res = await client.put(f"/api/v1/tax/profile/{person['id']}", json={
        "impatriate_enabled": True,
        "impatriate_arrival_date": "2023-09-01",
        "impatriate_election_method": "flat_30",
    })
    assert res.status_code == 200
    body = res.json()
    assert body["impatriate_enabled"] is True
    assert body["impatriate_arrival_date"] == "2023-09-01"
    assert body["impatriate_election_method"] == "flat_30"

    refetched = (await client.get(f"/api/v1/tax/profile/{person['id']}")).json()
    assert refetched == body


async def test_set_person_tax_profile_can_disable_and_clear_fields(client: AsyncClient) -> None:
    person = await _person(client)
    await client.put(f"/api/v1/tax/profile/{person['id']}", json={
        "impatriate_enabled": True,
        "impatriate_arrival_date": "2023-09-01",
        "impatriate_election_method": "flat_30",
    })

    res = await client.put(f"/api/v1/tax/profile/{person['id']}", json={
        "impatriate_enabled": False,
    })
    assert res.status_code == 200
    body = res.json()
    assert body["impatriate_enabled"] is False
    assert body["impatriate_arrival_date"] is None
    assert body["impatriate_election_method"] is None


async def test_set_tax_profile_missing_person_404s(client: AsyncClient) -> None:
    await _person(client)
    res = await client.put("/api/v1/tax/profile/999999", json={"impatriate_enabled": True})
    assert res.status_code == 404


async def test_household_tax_settings_defaults_to_single_no_dependents(
    client: AsyncClient,
) -> None:
    await _person(client)
    res = await client.get("/api/v1/tax/household-settings")
    assert res.status_code == 200
    body = res.json()
    assert body["filing_status"] == "single"
    assert body["dependent_person_ids"] == []


async def test_set_household_tax_settings_married_with_dependents(client: AsyncClient) -> None:
    antoine = await _person(client, "Antoine")
    kid = (await client.post(
        "/api/v1/persons", json={"name": "Theo", "is_primary": False}
    )).json()

    res = await client.put("/api/v1/tax/household-settings", json={
        "filing_status": "married_pacs",
        "dependent_person_ids": [kid["id"]],
    })
    assert res.status_code == 200
    body = res.json()
    assert body["filing_status"] == "married_pacs"
    assert body["dependent_person_ids"] == [kid["id"]]

    refetched = (await client.get("/api/v1/tax/household-settings")).json()
    assert refetched == body
    assert antoine["id"] not in refetched["dependent_person_ids"]


async def test_set_household_tax_settings_replaces_dependents_not_appends(
    client: AsyncClient,
) -> None:
    await _person(client, "Antoine")
    kid1 = (await client.post(
        "/api/v1/persons", json={"name": "Kid1", "is_primary": False}
    )).json()
    kid2 = (await client.post(
        "/api/v1/persons", json={"name": "Kid2", "is_primary": False}
    )).json()

    await client.put("/api/v1/tax/household-settings", json={
        "filing_status": "married_pacs",
        "dependent_person_ids": [kid1["id"]],
    })
    res = await client.put("/api/v1/tax/household-settings", json={
        "filing_status": "married_pacs",
        "dependent_person_ids": [kid2["id"]],
    })
    assert res.json()["dependent_person_ids"] == [kid2["id"]]


async def test_set_household_tax_settings_rejects_unknown_person_id(
    client: AsyncClient,
) -> None:
    await _person(client)
    res = await client.put("/api/v1/tax/household-settings", json={
        "filing_status": "single",
        "dependent_person_ids": [999999],
    })
    assert res.status_code == 422
