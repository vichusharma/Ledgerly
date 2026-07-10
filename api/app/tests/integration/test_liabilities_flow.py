"""Integration tests — liabilities (loans + amortization) domain."""
from __future__ import annotations

import datetime

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


def _loan_payload(owner_id: int, **overrides: object) -> dict:
    payload = {
        "name": "Prêt immobilier",
        "type": "mortgage",
        "principal": "280000",
        "annual_rate": "0.0185",
        "term_months": 240,
        "start_date": "2021-06-01",
        "payment_day": 5,
        "currency": "EUR",
        "owner_id": owner_id,
    }
    payload.update(overrides)
    return payload


async def test_create_loan_auto_creates_liability_account(client: AsyncClient) -> None:
    await _setup_and_login(client)
    person = await _create_person(client)

    res = await client.post("/api/v1/liabilities", json=_loan_payload(person["id"]))
    assert res.status_code == 201
    loan = res.json()
    assert loan["account_id"] is not None

    accounts = (await client.get("/api/v1/accounts")).json()
    linked = next(a for a in accounts if a["id"] == loan["account_id"])
    assert linked["type"] == "liability"
    assert linked["owner_id"] == person["id"]
    assert linked["name"] == "Prêt immobilier"

    schedule = (await client.get(f"/api/v1/liabilities/{loan['id']}/schedule")).json()
    assert len(schedule) == 240


async def test_create_loan_with_manual_payment(client: AsyncClient) -> None:
    await _setup_and_login(client)
    person = await _create_person(client)

    res = await client.post(
        "/api/v1/liabilities",
        json=_loan_payload(
            person["id"],
            principal="100000", annual_rate="0.03", term_months=120,
            start_date="2024-01-01", manual_payment="1100.00",
        ),
    )
    assert res.status_code == 201
    loan = res.json()

    schedule = (await client.get(f"/api/v1/liabilities/{loan['id']}/schedule")).json()
    assert schedule[0]["payment"] == "1100.0000"
    assert schedule[-1]["balance"] == "0.0000"


async def test_create_loan_invalid_manual_payment_422s(client: AsyncClient) -> None:
    await _setup_and_login(client)
    person = await _create_person(client)

    res = await client.post(
        "/api/v1/liabilities",
        json=_loan_payload(
            person["id"],
            principal="100000", annual_rate="0.03", term_months=120,
            start_date="2024-01-01", manual_payment="100.00",  # too low to cover interest
        ),
    )
    assert res.status_code == 422


async def test_prepayment_preview_is_non_destructive(client: AsyncClient) -> None:
    await _setup_and_login(client)
    person = await _create_person(client)
    loan = (await client.post("/api/v1/liabilities", json=_loan_payload(person["id"]))).json()

    before = (await client.get(f"/api/v1/liabilities/{loan['id']}/schedule")).json()

    res = await client.post(
        f"/api/v1/liabilities/{loan['id']}/prepay/preview",
        json={"amount": "10000", "reduction_mode": "term", "applied_date": "2026-06-05"},
    )
    assert res.status_code == 200
    preview = res.json()
    assert "reduce_term" in preview and "reduce_emi" in preview
    # reduce_term pays off sooner (fewer periods); reduce_emi keeps the original
    # period count but lowers the payment below the original steady EMI.
    assert preview["reduce_term"]["remaining_periods"] < preview["reduce_emi"]["remaining_periods"]
    assert float(preview["reduce_emi"]["new_payment"]) < float(before[100]["payment"])

    after = (await client.get(f"/api/v1/liabilities/{loan['id']}/schedule")).json()
    assert after == before


async def test_apply_prepayment_reduce_term_preserves_history(client: AsyncClient) -> None:
    await _setup_and_login(client)
    person = await _create_person(client)
    loan = (await client.post("/api/v1/liabilities", json=_loan_payload(person["id"]))).json()

    before = (await client.get(f"/api/v1/liabilities/{loan['id']}/schedule")).json()
    applied_date = before[59]["payment_date"]  # anchor at period 60

    res = await client.post(
        f"/api/v1/liabilities/{loan['id']}/prepay",
        json={"amount": "10000", "reduction_mode": "term", "applied_date": applied_date},
    )
    assert res.status_code == 200

    after = (await client.get(f"/api/v1/liabilities/{loan['id']}/schedule")).json()
    # Historical rows (periods 1-60) must be byte-for-byte unchanged.
    assert after[:60] == before[:60]
    # The remaining schedule should now be shorter (reduce-term).
    assert len(after) < len(before)
    # Payment held fixed for the recomputed future rows (except the final settle row).
    future_payments = {r["payment"] for r in after[60:-1]}
    assert future_payments == {before[60]["payment"]}


async def test_apply_prepayment_reduce_emi_preserves_history(client: AsyncClient) -> None:
    await _setup_and_login(client)
    person = await _create_person(client)
    loan = (await client.post("/api/v1/liabilities", json=_loan_payload(person["id"]))).json()

    before = (await client.get(f"/api/v1/liabilities/{loan['id']}/schedule")).json()
    applied_date = before[59]["payment_date"]

    res = await client.post(
        f"/api/v1/liabilities/{loan['id']}/prepay",
        json={"amount": "10000", "reduction_mode": "payment", "applied_date": applied_date},
    )
    assert res.status_code == 200

    after = (await client.get(f"/api/v1/liabilities/{loan['id']}/schedule")).json()
    assert after[:60] == before[:60]
    # Same period count as before (reduce-EMI keeps the term, lowers the payment).
    assert len(after) == len(before)
    assert float(after[60]["payment"]) < float(before[60]["payment"])


async def test_delete_loan_archives_linked_account(client: AsyncClient) -> None:
    await _setup_and_login(client)
    person = await _create_person(client)
    loan = (await client.post("/api/v1/liabilities", json=_loan_payload(person["id"]))).json()
    account_id = loan["account_id"]

    res = await client.delete(f"/api/v1/liabilities/{loan['id']}")
    assert res.status_code == 204

    accounts = (await client.get("/api/v1/accounts")).json()
    assert account_id not in [a["id"] for a in accounts]  # archived accounts excluded by default

    listing = (await client.get("/api/v1/liabilities")).json()
    assert loan["id"] not in [l["id"] for l in listing]


async def test_update_loan_cosmetic_fields(client: AsyncClient) -> None:
    await _setup_and_login(client)
    person = await _create_person(client)
    loan = (await client.post("/api/v1/liabilities", json=_loan_payload(person["id"]))).json()

    res = await client.patch(
        f"/api/v1/liabilities/{loan['id']}", json={"name": "Prêt renommé", "notes": "test"}
    )
    assert res.status_code == 200
    assert res.json()["name"] == "Prêt renommé"
    assert res.json()["notes"] == "test"
