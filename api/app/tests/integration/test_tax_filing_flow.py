"""Integration tests — per-person tax residency + treaty metadata
(Feature J1, facts only, no filing computation yet)."""
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


async def test_get_person_residency_defaults_no_home_country(
    client: AsyncClient,
) -> None:
    person = await _person(client)

    res = await client.get(f"/api/v1/tax-filing/residency/{person['id']}")
    assert res.status_code == 200
    body = res.json()
    assert body["person_id"] == person["id"]
    assert body["home_country_code"] is None
    assert body["home_country_tax_id"] is None
    assert body["french_tax_number"] is None


async def test_get_person_residency_missing_person_404s(client: AsyncClient) -> None:
    await _person(client)
    res = await client.get("/api/v1/tax-filing/residency/999999")
    assert res.status_code == 404


async def test_set_person_residency_persists_home_country_and_tax_ids(
    client: AsyncClient,
) -> None:
    person = await _person(client)

    res = await client.put(f"/api/v1/tax-filing/residency/{person['id']}", json={
        "home_country_code": "IN",
        "home_country_tax_id": "ABCDE1234F",
        "french_tax_number": "1234567890123",
    })
    assert res.status_code == 200
    body = res.json()
    assert body["home_country_code"] == "IN"
    assert body["home_country_tax_id"] == "ABCDE1234F"
    assert body["french_tax_number"] == "1234567890123"

    refetched = (await client.get(f"/api/v1/tax-filing/residency/{person['id']}")).json()
    assert refetched == body


async def test_set_person_residency_upserts_not_duplicates(client: AsyncClient) -> None:
    person = await _person(client)
    await client.put(f"/api/v1/tax-filing/residency/{person['id']}", json={
        "home_country_code": "IN",
    })
    res = await client.put(f"/api/v1/tax-filing/residency/{person['id']}", json={
        "home_country_code": "US",
    })
    assert res.status_code == 200
    assert res.json()["home_country_code"] == "US"

    refetched = (await client.get(f"/api/v1/tax-filing/residency/{person['id']}")).json()
    assert refetched["home_country_code"] == "US"


async def test_set_person_residency_missing_person_404s(client: AsyncClient) -> None:
    await _person(client)
    res = await client.put(
        "/api/v1/tax-filing/residency/999999", json={"home_country_code": "IN"}
    )
    assert res.status_code == 404


async def test_list_treaties_returns_seeded_countries(client: AsyncClient) -> None:
    await _person(client)
    res = await client.get("/api/v1/tax-filing/treaties")
    assert res.status_code == 200
    body = res.json()
    codes = {t["country_code"] for t in body}
    assert {"IN", "US", "GB", "CA", "DE"} <= codes
    india = next(t for t in body if t["country_code"] == "IN")
    assert india["default_elimination_method"] == "credit_equal_to_french_tax"
    germany = next(t for t in body if t["country_code"] == "DE")
    assert germany["default_elimination_method"] == "exemption_with_effective_rate"
