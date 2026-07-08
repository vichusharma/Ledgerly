"""Integration tests — RSU vesting + ESPP purchase confirm flows
(Feature J2-S1/S2, docs/Backlog.md)."""
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
    account = (await client.post("/api/v1/accounts", json={
        "name": "ESOP Account", "type": "investment_wrapper", "wrapper_type": "ESOP",
        "owner_id": person["id"],
    })).json()
    instrument = (await client.post("/api/v1/instruments", json={
        "isin": "US0000000001", "ticker": "ACME", "name": "Acme Corp",
    })).json()
    return {"person": person, "account": account, "instrument": instrument}


async def test_confirm_rsu_vesting_creates_schedule_and_lot(client: AsyncClient) -> None:
    ctx = await _setup(client)
    payload = {
        "person_id": ctx["person"]["id"],
        "account_id": ctx["account"]["id"],
        "instrument_id": ctx["instrument"]["id"],
        "tax_year": 2026,
        "grant_date": "2023-01-15",
        "total_shares": "400",
        "cliff_months": 12,
        "vesting_months": 48,
        "grant_price": "45.00",
        "vest_date": "2026-01-15",
        "vested_shares": "100",
        "vest_fmv": "62.50",
    }
    import json
    res = await client.post(
        "/api/v1/tax-filing/rsu-vesting",
        files={"file": ("vest.pdf", b"%PDF-1.4 fake rsu bytes", "application/pdf")},
        data={"payload": json.dumps(payload)},
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["vested_shares"] == "100"
    assert body["vest_fmv"] == "62.50"

    lots = (await client.get(
        "/api/v1/investment-lots", params={"account_id": ctx["account"]["id"]}
    )).json()
    assert any(lot["lot_type"] == "vesting" for lot in lots)


async def test_confirm_rsu_vesting_reconfirm_upserts_schedule(client: AsyncClient) -> None:
    ctx = await _setup(client)
    import json
    payload = {
        "person_id": ctx["person"]["id"],
        "account_id": ctx["account"]["id"],
        "instrument_id": ctx["instrument"]["id"],
        "tax_year": 2026,
        "grant_date": "2023-01-15",
        "total_shares": "400",
        "cliff_months": 12,
        "vesting_months": 48,
        "grant_price": "45.00",
        "vest_date": "2026-01-15",
        "vested_shares": "100",
        "vest_fmv": "62.50",
    }
    first = await client.post(
        "/api/v1/tax-filing/rsu-vesting",
        files={"file": ("vest.pdf", b"%PDF-1.4 fake rsu bytes", "application/pdf")},
        data={"payload": json.dumps(payload)},
    )
    payload2 = {**payload, "vest_date": "2026-04-15", "vested_shares": "100"}
    second = await client.post(
        "/api/v1/tax-filing/rsu-vesting",
        files={"file": ("vest2.pdf", b"%PDF-1.4 fake rsu bytes 2", "application/pdf")},
        data={"payload": json.dumps(payload2)},
    )
    assert second.status_code == 201, second.text
    # Same grant -> same vesting_schedule_id, not a duplicate schedule.
    assert first.json()["vesting_schedule_id"] == second.json()["vesting_schedule_id"]


async def test_confirm_espp_purchase_creates_buy_lot_with_espp_fields(
    client: AsyncClient,
) -> None:
    ctx = await _setup(client)
    import json
    payload = {
        "person_id": ctx["person"]["id"],
        "account_id": ctx["account"]["id"],
        "instrument_id": ctx["instrument"]["id"],
        "tax_year": 2026,
        "purchase_date": "2026-06-30",
        "shares": "25.75",
        "purchase_price": "38.25",
        "fmv_at_purchase": "45.00",
        "discount_pct": "15",
    }
    res = await client.post(
        "/api/v1/tax-filing/espp-purchases",
        files={"file": ("espp.pdf", b"%PDF-1.4 fake espp bytes", "application/pdf")},
        data={"payload": json.dumps(payload)},
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["shares"] == "25.75"
    assert body["fmv_at_acquisition"] == "45.00"
    assert body["discount_pct"] == "15"
