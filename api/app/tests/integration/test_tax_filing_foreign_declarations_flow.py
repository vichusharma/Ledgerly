"""Integration tests — foreign income (Form 2047) and foreign account
(Form 3916) declarations, manual CRUD + parser-confirm (Feature J2-S3,
J2-S4, J2-S7, docs/Backlog.md)."""
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


# -- Foreign income -----------------------------------------------------

async def test_create_foreign_income_manual_entry(client: AsyncClient) -> None:
    person = await _person(client)
    res = await client.post("/api/v1/tax-filing/foreign-income", json={
        "person_id": person["id"], "tax_year": 2026,
        "income_type": "foreign_dividend", "source_country_code": "US",
        "source_description": "Acme Corp", "gross_amount_eur": "500.00",
        "foreign_tax_paid_eur": "75.00",
    })
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["source_description"] == "Acme Corp"
    assert body["gross_amount_eur"] == "500.00"


async def test_confirm_foreign_income_stores_document(client: AsyncClient) -> None:
    person = await _person(client)
    payload = {
        "person_id": person["id"], "tax_year": 2026,
        "income_type": "foreign_dividend", "source_country_code": "IN",
        "source_description": "Infosys", "gross_amount_eur": "200.00",
        "foreign_tax_paid_eur": "20.00",
    }
    res = await client.post(
        "/api/v1/tax-filing/foreign-income/confirm",
        files={"file": ("div.pdf", b"%PDF-1.4 fake dividend statement", "application/pdf")},
        data={"payload": json.dumps(payload)},
    )
    assert res.status_code == 201, res.text
    assert res.json()["source_description"] == "Infosys"


async def test_list_update_delete_foreign_income(client: AsyncClient) -> None:
    person = await _person(client)
    created = (await client.post("/api/v1/tax-filing/foreign-income", json={
        "person_id": person["id"], "tax_year": 2026,
        "income_type": "foreign_interest", "source_country_code": "GB",
        "source_description": "Barclays", "gross_amount_eur": "100.00",
    })).json()

    listed = (await client.get(
        "/api/v1/tax-filing/foreign-income", params={"person_id": person["id"]}
    )).json()
    assert any(item["id"] == created["id"] for item in listed)

    updated = (await client.put(
        f"/api/v1/tax-filing/foreign-income/{created['id']}",
        json={"gross_amount_eur": "150.00"},
    )).json()
    assert updated["gross_amount_eur"] == "150.00"
    assert updated["source_description"] == "Barclays"

    del_res = await client.delete(f"/api/v1/tax-filing/foreign-income/{created['id']}")
    assert del_res.status_code == 204
    missing_del = await client.delete(f"/api/v1/tax-filing/foreign-income/{created['id']}")
    assert missing_del.status_code == 404


# -- Foreign accounts -----------------------------------------------------

async def test_create_foreign_account_manual_entry(client: AsyncClient) -> None:
    person = await _person(client)
    res = await client.post("/api/v1/tax-filing/foreign-accounts", json={
        "person_id": person["id"], "tax_year": 2026,
        "bank_name": "State Bank of India", "country_code": "IN",
        "account_identifier_masked": "****3456",
    })
    assert res.status_code == 201, res.text
    assert res.json()["bank_name"] == "State Bank of India"


async def test_confirm_foreign_account_stores_document(client: AsyncClient) -> None:
    person = await _person(client)
    payload = {
        "person_id": person["id"], "tax_year": 2026,
        "bank_name": "HSBC UK", "country_code": "GB",
        "account_identifier_masked": "****1111",
    }
    res = await client.post(
        "/api/v1/tax-filing/foreign-accounts/confirm",
        files={"file": ("stmt.pdf", b"%PDF-1.4 fake bank statement", "application/pdf")},
        data={"payload": json.dumps(payload)},
    )
    assert res.status_code == 201, res.text
    assert res.json()["bank_name"] == "HSBC UK"


async def test_list_update_delete_foreign_account(client: AsyncClient) -> None:
    person = await _person(client)
    created = (await client.post("/api/v1/tax-filing/foreign-accounts", json={
        "person_id": person["id"], "tax_year": 2026,
        "bank_name": "Deutsche Bank", "country_code": "DE",
    })).json()

    listed = (await client.get(
        "/api/v1/tax-filing/foreign-accounts", params={"tax_year": 2026}
    )).json()
    assert any(item["id"] == created["id"] for item in listed)

    updated = (await client.put(
        f"/api/v1/tax-filing/foreign-accounts/{created['id']}",
        json={"closed_this_year": True},
    )).json()
    assert updated["closed_this_year"] is True

    del_res = await client.delete(f"/api/v1/tax-filing/foreign-accounts/{created['id']}")
    assert del_res.status_code == 204
    missing_del = await client.delete(f"/api/v1/tax-filing/foreign-accounts/{created['id']}")
    assert missing_del.status_code == 404


async def test_foreign_account_links_to_existing_ledgerly_account(
    client: AsyncClient,
) -> None:
    person = await _person(client)
    account = (await client.post("/api/v1/accounts", json={
        "name": "Indian Savings", "type": "bank", "owner_id": person["id"],
        "country_code": "IN",
    })).json()
    assert account["country_code"] == "IN"

    declaration = (await client.post("/api/v1/tax-filing/foreign-accounts", json={
        "person_id": person["id"], "tax_year": 2026, "account_id": account["id"],
        "bank_name": "ICICI Bank", "country_code": "IN",
    })).json()
    assert declaration["account_id"] == account["id"]
