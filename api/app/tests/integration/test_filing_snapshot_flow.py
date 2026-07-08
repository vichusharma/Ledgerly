"""Integration tests — FilingSnapshot compute/validate/lock (Feature
J5, docs/Backlog.md). Builds on top of Epic I's `/tax/estimate` and
Feature J4's `tax_filing_rules` engine — no new tax math here, just
wiring + persistence."""
from __future__ import annotations

import json

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


async def test_compute_filing_creates_snapshot(client: AsyncClient) -> None:
    await _person(client)
    res = await client.post("/api/v1/tax-filing/compute", params={"year": 2026})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["tax_year"] == 2026
    assert body["locked"] is False
    assert "estimated_tax" in body["payload"]
    assert body["payload"]["boxes_2042"] == []


async def test_get_filing_before_compute_404s(client: AsyncClient) -> None:
    await _person(client)
    res = await client.get("/api/v1/tax-filing/forms/2026")
    assert res.status_code == 404


async def test_get_filing_after_compute(client: AsyncClient) -> None:
    await _person(client)
    await client.post("/api/v1/tax-filing/compute", params={"year": 2026})
    res = await client.get("/api/v1/tax-filing/forms/2026")
    assert res.status_code == 200
    assert res.json()["tax_year"] == 2026


async def test_recompute_upserts_not_duplicates(client: AsyncClient) -> None:
    await _person(client)
    first = await client.post("/api/v1/tax-filing/compute", params={"year": 2026})
    second = await client.post("/api/v1/tax-filing/compute", params={"year": 2026})
    assert first.json()["tax_year"] == second.json()["tax_year"] == 2026


async def test_lock_then_recompute_409s(client: AsyncClient) -> None:
    await _person(client)
    await client.post("/api/v1/tax-filing/compute", params={"year": 2026})
    lock_res = await client.post("/api/v1/tax-filing/forms/2026/lock")
    assert lock_res.status_code == 200
    assert lock_res.json()["locked"] is True

    recompute = await client.post("/api/v1/tax-filing/compute", params={"year": 2026})
    assert recompute.status_code == 409


async def test_unlock_allows_recompute(client: AsyncClient) -> None:
    await _person(client)
    await client.post("/api/v1/tax-filing/compute", params={"year": 2026})
    await client.post("/api/v1/tax-filing/forms/2026/lock")

    unlock_res = await client.post("/api/v1/tax-filing/forms/2026/unlock")
    assert unlock_res.status_code == 200
    assert unlock_res.json()["locked"] is False

    recompute = await client.post("/api/v1/tax-filing/compute", params={"year": 2026})
    assert recompute.status_code == 200


async def test_lock_unlock_missing_year_404s(client: AsyncClient) -> None:
    await _person(client)
    assert (await client.post("/api/v1/tax-filing/forms/2099/lock")).status_code == 404
    assert (await client.post("/api/v1/tax-filing/forms/2099/unlock")).status_code == 404


async def test_validate_flags_missing_residency_and_undeclared_country(
    client: AsyncClient,
) -> None:
    person = await _person(client)
    await client.post("/api/v1/tax-filing/foreign-income/confirm", files={
        "file": ("div.pdf", b"%PDF-1.4 fake", "application/pdf")
    }, data={"payload": json.dumps({
        "person_id": person["id"], "tax_year": 2026,
        "income_type": "foreign_dividend", "source_country_code": "US",
        "source_description": "Acme Corp", "gross_amount_eur": "500.00",
    })})

    res = await client.post("/api/v1/tax-filing/validate", params={"year": 2026})
    assert res.status_code == 200
    issues = res.json()
    assert "missing_residency_profile" in issues
    assert "foreign_income_from_US_with_no_declared_account" in issues
    # Confirmed via the parser-confirm path, so a source document does
    # exist — no "missing document" issue for this line.
    assert not any(i.startswith("no_source_document_for_foreign_income_") for i in issues)


async def test_validate_clean_when_residency_and_account_and_document_present(
    client: AsyncClient,
) -> None:
    person = await _person(client)
    await client.put(f"/api/v1/tax-filing/residency/{person['id']}", json={
        "home_country_code": "US",
    })
    await client.post("/api/v1/tax-filing/foreign-accounts", json={
        "person_id": person["id"], "tax_year": 2026,
        "bank_name": "Chase", "country_code": "US",
    })
    await client.post("/api/v1/tax-filing/foreign-income/confirm", files={
        "file": ("div.pdf", b"%PDF-1.4 fake", "application/pdf")
    }, data={"payload": json.dumps({
        "person_id": person["id"], "tax_year": 2026,
        "income_type": "foreign_dividend", "source_country_code": "US",
        "source_description": "Acme Corp", "gross_amount_eur": "500.00",
    })})

    res = await client.post("/api/v1/tax-filing/validate", params={"year": 2026})
    issues = res.json()
    assert "missing_residency_profile" not in issues
    assert "foreign_income_from_US_with_no_declared_account" not in issues
    assert not any(i.startswith("no_source_document_for_foreign_income_") for i in issues)
