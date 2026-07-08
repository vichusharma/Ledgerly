"""Integration tests — encrypted document list/download/delete (Feature
J3-S3/S4, docs/Backlog.md), first real endpoints on top of J3-S1/S2's
storage layer built via Feature J2's confirm flows."""
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


async def _confirm_foreign_income_with_document(
    client: AsyncClient, person_id: int, content: bytes = b"%PDF-1.4 fake dividend stmt"
) -> dict:
    payload = {
        "person_id": person_id, "tax_year": 2026,
        "income_type": "foreign_dividend", "source_country_code": "IN",
        "source_description": "Infosys", "gross_amount_eur": "200.00",
    }
    res = await client.post(
        "/api/v1/tax-filing/foreign-income/confirm",
        files={"file": ("div.pdf", content, "application/pdf")},
        data={"payload": json.dumps(payload)},
    )
    assert res.status_code == 201, res.text
    return res.json()


async def test_list_documents_after_confirm(client: AsyncClient) -> None:
    person = await _person(client)
    await _confirm_foreign_income_with_document(client, person["id"])

    listed = (await client.get(
        "/api/v1/tax-filing/documents", params={"person_id": person["id"]}
    )).json()
    assert len(listed) == 1
    assert listed[0]["document_type"] == "foreign_dividend"
    assert listed[0]["original_filename"] == "div.pdf"


async def test_download_document_decrypts_original_bytes(client: AsyncClient) -> None:
    person = await _person(client)
    original = b"%PDF-1.4 the real fake dividend statement bytes"
    await _confirm_foreign_income_with_document(client, person["id"], original)

    listed = (await client.get(
        "/api/v1/tax-filing/documents", params={"person_id": person["id"]}
    )).json()
    doc_id = listed[0]["id"]

    res = await client.get(f"/api/v1/tax-filing/documents/{doc_id}/download")
    assert res.status_code == 200
    assert res.content == original
    assert res.headers["content-type"] == "application/pdf"
    assert "div.pdf" in res.headers["content-disposition"]


async def test_download_missing_document_404s(client: AsyncClient) -> None:
    await _person(client)
    res = await client.get("/api/v1/tax-filing/documents/999999/download")
    assert res.status_code == 404


async def test_delete_document(client: AsyncClient) -> None:
    person = await _person(client)
    await _confirm_foreign_income_with_document(client, person["id"])
    listed = (await client.get(
        "/api/v1/tax-filing/documents", params={"person_id": person["id"]}
    )).json()
    doc_id = listed[0]["id"]

    del_res = await client.delete(f"/api/v1/tax-filing/documents/{doc_id}")
    assert del_res.status_code == 204
    missing_del = await client.delete(f"/api/v1/tax-filing/documents/{doc_id}")
    assert missing_del.status_code == 404
    assert (await client.get(f"/api/v1/tax-filing/documents/{doc_id}/download")).status_code == 404
