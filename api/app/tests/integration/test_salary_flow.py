"""Integration tests — payslip save/upsert/list/delete flow."""
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


async def test_save_payslip_creates_record(client: AsyncClient) -> None:
    person = await _person(client)

    res = await client.post("/api/v1/salary/payslips", json={
        "person_id": person["id"],
        "pay_period": "2026-06-01",
        "employer": "Acme France SAS",
        "gross": "5000.00",
        "net_taxable": "4200.00",
        "net_before_tax": "2987.20",
        "net_paid": "2650.10",
        "pas_rate": "10.80",
        "pas_withheld": "692.60",
        "ytd_gross": "30000.00",
        "ytd_net_taxable": "25200.00",
        "ytd_pas_withheld": "2394.00",
    })
    assert res.status_code == 201
    body = res.json()
    assert body["person_id"] == person["id"]
    assert body["pay_period"] == "2026-06-01"
    assert float(body["gross"]) == 5000.00
    assert float(body["pas_withheld"]) == 692.60


async def test_resave_same_person_period_upserts_not_duplicates(client: AsyncClient) -> None:
    person = await _person(client)
    payload = {
        "person_id": person["id"],
        "pay_period": "2026-06-01",
        "gross": "5000.00",
    }
    await client.post("/api/v1/salary/payslips", json=payload)

    # Corrected review of the same month → update in place, not a duplicate.
    payload["gross"] = "8000.00"
    await client.post("/api/v1/salary/payslips", json=payload)

    listed = (await client.get(
        "/api/v1/salary/payslips", params={"person_id": person["id"]}
    )).json()
    assert len(listed) == 1
    assert float(listed[0]["gross"]) == 8000.00


async def test_list_filters_by_person_and_year(client: AsyncClient) -> None:
    antoine = await _person(client, "Antoine")
    nancy = (await client.post(
        "/api/v1/persons", json={"name": "Camille", "is_primary": False}
    )).json()

    for person_id, period in (
        (antoine["id"], "2025-12-01"),
        (antoine["id"], "2026-06-01"),
        (nancy["id"], "2026-06-01"),
    ):
        await client.post("/api/v1/salary/payslips", json={
            "person_id": person_id, "pay_period": period, "gross": "5000.00",
        })

    antoine_2026 = (await client.get(
        "/api/v1/salary/payslips", params={"person_id": antoine["id"], "year": 2026}
    )).json()
    assert len(antoine_2026) == 1
    assert antoine_2026[0]["pay_period"] == "2026-06-01"

    all_2026 = (await client.get("/api/v1/salary/payslips", params={"year": 2026})).json()
    assert len(all_2026) == 2


async def test_delete_payslip(client: AsyncClient) -> None:
    person = await _person(client)
    saved = (await client.post("/api/v1/salary/payslips", json={
        "person_id": person["id"], "pay_period": "2026-06-01", "gross": "5000.00",
    })).json()

    res = await client.delete(f"/api/v1/salary/payslips/{saved['id']}")
    assert res.status_code == 204

    listed = (await client.get(
        "/api/v1/salary/payslips", params={"person_id": person["id"]}
    )).json()
    assert listed == []


async def test_delete_missing_payslip_404s(client: AsyncClient) -> None:
    await _person(client)
    res = await client.delete("/api/v1/salary/payslips/999999")
    assert res.status_code == 404
