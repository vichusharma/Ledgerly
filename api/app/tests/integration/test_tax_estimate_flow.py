"""Integration tests — GET /tax/estimate (Feature I3, salary-only PAS
reconciliation). Golden values hand-computed against the seeded 2026
placeholder barème (0%/11%/30%/41%/45%, thresholds 11497/29315/83823/
180294) and a 1,791 EUR quotient-familial plafonnement per half-part."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

PASSWORD = "S3cur3P@ss!"


async def _person(client: AsyncClient, name: str = "Antoine", is_primary: bool = True) -> dict:
    return (await client.post(
        "/api/v1/persons", json={"name": name, "is_primary": is_primary}
    )).json()


async def _login(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/setup", json={"password": PASSWORD})
    await client.post("/api/v1/auth/login", json={"password": PASSWORD})


async def _payslip(
    client: AsyncClient, person_id: int, pay_period: str,
    ytd_gross: str, ytd_net_taxable: str, ytd_pas_withheld: str,
) -> None:
    res = await client.post("/api/v1/salary/payslips", json={
        "person_id": person_id,
        "pay_period": pay_period,
        "ytd_gross": ytd_gross,
        "ytd_net_taxable": ytd_net_taxable,
        "ytd_pas_withheld": ytd_pas_withheld,
    })
    assert res.status_code == 201


async def test_single_person_default_filing_status(client: AsyncClient) -> None:
    await _login(client)
    person = await _person(client)
    await _payslip(client, person["id"], "2026-06-01", "60000", "54000", "5000")

    res = await client.get("/api/v1/tax/estimate", params={"year": 2026})
    assert res.status_code == 200
    body = res.json()

    assert body["filing_status"] == "single"
    assert body["parts"] is None
    assert float(body["household_taxable_income_projected"]) == 108000.00
    assert float(body["household_gross_income_projected"]) == 120000.00
    assert float(body["estimated_tax"]) == 28224.95
    assert body["quotient_familial_capped"] is False
    assert float(body["pas_withheld_ytd_total"]) == 5000.00
    assert float(body["pas_withheld_projected_annual_total"]) == 10000.00
    assert float(body["balance"]) == 18224.95
    assert body["bareme_tax_year_used"] == 2026
    assert body["investment_income"] is None
    assert "capital_gains_not_included" in body["simplifications_applied"]

    assert len(body["persons"]) == 1
    p = body["persons"][0]
    assert p["person_id"] == person["id"]
    assert p["has_payslip_data"] is True
    assert p["as_of_month"] == 6
    assert float(p["parts_used"]) == 1.0
    assert p["impatriate_enabled"] is False


async def test_married_pacs_combines_two_persons(client: AsyncClient) -> None:
    await _login(client)
    antoine = await _person(client, "Antoine", True)
    nancy = await _person(client, "Camille", False)
    await _payslip(client, antoine["id"], "2026-03-01", "30000", "27000", "2000")
    await _payslip(client, nancy["id"], "2026-03-01", "15000", "13500", "1000")

    await client.put("/api/v1/tax/household-settings", json={
        "filing_status": "married_pacs", "dependent_person_ids": [],
    })

    res = await client.get("/api/v1/tax/estimate", params={"year": 2026})
    body = res.json()

    assert body["filing_status"] == "married_pacs"
    assert float(body["parts"]) == 2.0
    assert float(body["household_taxable_income_projected"]) == 162000.00
    assert float(body["household_gross_income_projected"]) == 180000.00
    assert float(body["estimated_tax"]) == 34930.96
    assert body["quotient_familial_capped"] is False
    assert float(body["pas_withheld_ytd_total"]) == 3000.00
    assert float(body["pas_withheld_projected_annual_total"]) == 12000.00
    assert float(body["balance"]) == 22930.96

    assert len(body["persons"]) == 2
    for p in body["persons"]:
        assert float(p["parts_used"]) == 2.0


async def test_impatriate_flat_30_reduces_taxable_income(client: AsyncClient) -> None:
    await _login(client)
    person = await _person(client)
    await _payslip(client, person["id"], "2026-06-01", "60000", "54000", "5000")
    await client.put(f"/api/v1/tax/profile/{person['id']}", json={
        "impatriate_enabled": True,
        "impatriate_arrival_date": "2023-09-01",
        "impatriate_election_method": "flat_30",
    })

    res = await client.get("/api/v1/tax/estimate", params={"year": 2026})
    body = res.json()

    p = body["persons"][0]
    assert p["impatriate_enabled"] is True
    assert p["impatriate_exemption_applied"] is True
    assert float(p["net_taxable_annual_projected"]) == 108000.00
    assert float(p["net_taxable_after_impatriate"]) == 75600.00
    assert p["impatriate_years_remaining"] == 4

    assert float(body["household_taxable_income_projected"]) == 75600.00
    assert float(body["estimated_tax"]) == 15845.48


async def test_specific_premium_not_computed_flags_simplification(client: AsyncClient) -> None:
    await _login(client)
    person = await _person(client)
    await _payslip(client, person["id"], "2026-06-01", "60000", "54000", "5000")
    await client.put(f"/api/v1/tax/profile/{person['id']}", json={
        "impatriate_enabled": True,
        "impatriate_arrival_date": "2023-09-01",
        "impatriate_election_method": "specific_premium",
    })

    res = await client.get("/api/v1/tax/estimate", params={"year": 2026})
    body = res.json()

    p = body["persons"][0]
    assert p["impatriate_exemption_applied"] is False
    assert float(p["net_taxable_after_impatriate"]) == float(p["net_taxable_annual_projected"])
    assert "impatriate_specific_premium_not_computed" in body["simplifications_applied"]


async def test_person_without_payslip_data_contributes_zero(client: AsyncClient) -> None:
    await _login(client)
    antoine = await _person(client, "Antoine", True)
    await _person(client, "Camille", False)
    await _payslip(client, antoine["id"], "2026-06-01", "60000", "54000", "5000")

    res = await client.get("/api/v1/tax/estimate", params={"year": 2026})
    body = res.json()

    assert len(body["persons"]) == 2
    nancy_entry = next(p for p in body["persons"] if p["name"] == "Camille")
    assert nancy_entry["has_payslip_data"] is False
    assert nancy_entry["as_of_month"] is None
    assert float(nancy_entry["gross_annual_projected"]) == 0.0
    assert float(nancy_entry["pas_withheld_projected_annual"]) == 0.0


async def test_unknown_year_falls_back_to_latest_config(client: AsyncClient) -> None:
    await _login(client)
    await _person(client)

    res = await client.get("/api/v1/tax/estimate", params={"year": 2030})
    assert res.status_code == 200
    body = res.json()
    assert body["year"] == 2030
    assert body["bareme_tax_year_used"] == 2026
    assert "bareme_year_fallback" in body["simplifications_applied"]
