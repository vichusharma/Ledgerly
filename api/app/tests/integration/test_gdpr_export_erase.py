"""Integration tests — GDPR export/erase now cover Epic I + Epic J's
personal-data tables (Feature J3-S5, docs/Backlog.md). Previously
`erase_all_data()`'s hard-coded table list didn't even include Epic I's
own tables (`payslips`, `household_tax_settings`, ...) — this session
closes that gap alongside adding Epic J's new tables."""
from __future__ import annotations

import io
import json
import zipfile

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

PASSWORD = "S3cur3P@ss!"


async def _setup_with_foreign_income(client: AsyncClient) -> dict:
    await client.post("/api/v1/auth/setup", json={"password": PASSWORD})
    await client.post("/api/v1/auth/login", json={"password": PASSWORD})
    person = (await client.post(
        "/api/v1/persons", json={"name": "Antoine", "is_primary": True}
    )).json()
    await client.post("/api/v1/tax-filing/foreign-income/confirm", files={
        "file": ("div.pdf", b"%PDF-1.4 fake dividend stmt", "application/pdf")
    }, data={"payload": json.dumps({
        "person_id": person["id"], "tax_year": 2026,
        "income_type": "foreign_dividend", "source_country_code": "IN",
        "source_description": "Infosys", "gross_amount_eur": "200.00",
    })})
    await client.put(f"/api/v1/tax-filing/residency/{person['id']}", json={
        "home_country_code": "IN",
    })
    return person


async def test_export_includes_tax_filing_data(client: AsyncClient) -> None:
    await _setup_with_foreign_income(client)
    res = await client.get("/api/v1/export")
    assert res.status_code == 200
    zf = zipfile.ZipFile(io.BytesIO(res.content))
    names = zf.namelist()
    assert "person_tax_residency.json" in names
    assert "foreign_income_declarations.json" in names
    assert "tax_documents/manifest.json" in names

    income = json.loads(zf.read("foreign_income_declarations.json"))
    assert income[0]["source_description"] == "Infosys"

    manifest = json.loads(zf.read("tax_documents/manifest.json"))
    assert len(manifest) == 1
    doc_files = [
        n for n in names
        if n.startswith("tax_documents/") and n != "tax_documents/manifest.json"
    ]
    assert zf.read(doc_files[0]) == b"%PDF-1.4 fake dividend stmt"


async def test_erase_all_data_clears_tax_filing_tables(client: AsyncClient) -> None:
    person = await _setup_with_foreign_income(client)

    res = await client.delete("/api/v1/account/data")
    assert res.status_code == 204

    # Household/persons wiped -> residency lookup 404s (person gone).
    residency_res = await client.get(f"/api/v1/tax-filing/residency/{person['id']}")
    assert residency_res.status_code == 404

    income = (await client.get("/api/v1/tax-filing/foreign-income")).json()
    assert income == []

    docs = (await client.get("/api/v1/tax-filing/documents")).json()
    assert docs == []
