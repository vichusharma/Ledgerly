"""Integration tests — GET /tax/estimate (Feature I3, salary-only PAS
reconciliation). Golden values hand-computed against the seeded 2026
placeholder barème (0%/11%/30%/41%/45%, thresholds 11497/29315/83823/
180294) and a 1,791 EUR quotient-familial plafonnement per half-part."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

PASSWORD = "S3cur3P@ss!"


async def _person(
    client: AsyncClient, name: str = "Antoine", is_primary: bool = True,
    date_of_birth: str | None = None,
) -> dict:
    return (await client.post(
        "/api/v1/persons",
        json={"name": name, "is_primary": is_primary, "date_of_birth": date_of_birth},
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


# ── Feature I4: investment income folded in ────────────────────────────────


async def _account(
    client: AsyncClient, owner_id: int, wrapper_type: str, opened_at: str,
) -> dict:
    res = await client.post("/api/v1/accounts", json={
        "name": f"{wrapper_type} account", "type": "investment_wrapper",
        "wrapper_type": wrapper_type, "owner_id": owner_id, "opened_at": opened_at,
    })
    assert res.status_code == 201
    return res.json()


async def _buy_lot(
    client: AsyncClient, account_id: int, isin: str, quantity: str, price: str, settled_at: str,
) -> int:
    res = await client.post("/api/v1/portfolio/holdings", json={
        "isin": isin, "quantity": quantity, "account_id": account_id,
        "price": price, "name": isin, "settled_at": settled_at,
    })
    assert res.status_code == 201
    return res.json()["instrument"]["id"]


async def _sell_lot(
    client: AsyncClient, account_id: int, instrument_id: int,
    quantity: str, price: str, settled_at: str,
) -> None:
    res = await client.post("/api/v1/investment-lots", json={
        "account_id": account_id, "instrument_id": instrument_id,
        "lot_type": "sell", "quantity": quantity, "price": price, "settled_at": settled_at,
    })
    assert res.status_code == 201


async def _dividend_lot(client: AsyncClient, account_id: int, amount: str, settled_at: str) -> None:
    res = await client.post("/api/v1/investment-lots", json={
        "account_id": account_id, "instrument_id": None,
        "lot_type": "dividend", "quantity": "1", "price": amount, "settled_at": settled_at,
    })
    assert res.status_code == 201


async def test_no_investment_lots_is_a_noop(client: AsyncClient) -> None:
    await _login(client)
    person = await _person(client)
    await _payslip(client, person["id"], "2026-06-01", "60000", "54000", "5000")

    without = (await client.get(
        "/api/v1/tax/estimate", params={"year": 2026, "include_investments": False}
    )).json()
    with_inv = (await client.get(
        "/api/v1/tax/estimate", params={"year": 2026, "include_investments": True}
    )).json()

    assert with_inv["investment_income"] is not None
    assert float(with_inv["investment_income"]["realized_gains_total"]) == 0.0
    assert float(with_inv["investment_income"]["dividends_total"]) == 0.0
    assert float(with_inv["investment_income"]["taxable_investment_income"]) == 0.0
    assert with_inv["investment_income"]["chosen_method"] == "pfu"
    assert float(with_inv["estimated_tax"]) == float(without["estimated_tax"])
    assert without["investment_income"] is None


async def test_cto_realized_gain_taxed_via_pfu(client: AsyncClient) -> None:
    await _login(client)
    person = await _person(client)
    await _payslip(client, person["id"], "2026-06-01", "60000", "54000", "5000")

    acct = await _account(client, person["id"], "CTO", "2020-01-01")
    instrument_id = await _buy_lot(client, acct["id"], "IE00B4L5Y983", "10", "100", "2025-01-01")
    await _sell_lot(client, acct["id"], instrument_id, "10", "150", "2026-06-01")

    res = await client.get(
        "/api/v1/tax/estimate", params={"year": 2026, "include_investments": True}
    )
    body = res.json()
    inv = body["investment_income"]

    assert float(inv["realized_gains_total"]) == 500.0
    assert float(inv["taxable_investment_income"]) == 500.0
    assert inv["exemptions_applied"] == []
    # PFU should be cheaper here (12.8% flat vs. a household already taxed
    # in higher brackets from a 60k salary) — the estimate should reflect it.
    assert inv["chosen_method"] == "pfu"
    assert float(inv["pfu_total_tax"]) - float(inv["bareme_option_total_tax"]) <= 0


async def test_pea_past_five_years_is_fully_exempt(client: AsyncClient) -> None:
    await _login(client)
    person = await _person(client)
    await _payslip(client, person["id"], "2026-06-01", "60000", "54000", "5000")

    acct = await _account(client, person["id"], "PEA", "2015-01-01")
    instrument_id = await _buy_lot(client, acct["id"], "IE00B4L5Y983", "10", "100", "2020-01-01")
    await _sell_lot(client, acct["id"], instrument_id, "10", "150", "2026-06-01")

    res = await client.get(
        "/api/v1/tax/estimate", params={"year": 2026, "include_investments": True}
    )
    inv = res.json()["investment_income"]

    assert float(inv["realized_gains_total"]) == 500.0
    assert float(inv["taxable_investment_income"]) == 0.0
    assert "pea_five_year_exemption" in inv["exemptions_applied"]


async def test_av_past_eight_years_gets_abattement(client: AsyncClient) -> None:
    await _login(client)
    person = await _person(client)
    await _payslip(client, person["id"], "2026-06-01", "60000", "54000", "5000")

    acct = await _account(client, person["id"], "AV", "2010-01-01")
    instrument_id = await _buy_lot(client, acct["id"], "IE00B4L5Y983", "10", "100", "2020-01-01")
    await _sell_lot(client, acct["id"], instrument_id, "10", "700", "2026-06-01")

    res = await client.get(
        "/api/v1/tax/estimate", params={"year": 2026, "include_investments": True}
    )
    inv = res.json()["investment_income"]

    # gain = (700-100)*10 = 6000; single abattement 4600 -> taxable 1400
    assert float(inv["realized_gains_total"]) == 6000.0
    assert float(inv["taxable_investment_income"]) == 1400.0
    assert "av_eight_year_abattement" in inv["exemptions_applied"]


async def test_dividends_included_in_taxable_income(client: AsyncClient) -> None:
    await _login(client)
    person = await _person(client)
    await _payslip(client, person["id"], "2026-06-01", "60000", "54000", "5000")

    acct = await _account(client, person["id"], "CTO", "2020-01-01")
    await _dividend_lot(client, acct["id"], "200", "2026-04-01")

    res = await client.get(
        "/api/v1/tax/estimate", params={"year": 2026, "include_investments": True}
    )
    inv = res.json()["investment_income"]

    assert float(inv["dividends_total"]) == 200.0
    assert float(inv["taxable_investment_income"]) == 200.0


async def test_married_pacs_pools_investment_income_at_household_level(client: AsyncClient) -> None:
    await _login(client)
    antoine = await _person(client, "Antoine", True)
    nancy = await _person(client, "Camille", False)
    await _payslip(client, antoine["id"], "2026-06-01", "30000", "27000", "2000")
    await _payslip(client, nancy["id"], "2026-06-01", "15000", "13500", "1000")
    await client.put("/api/v1/tax/household-settings", json={
        "filing_status": "married_pacs", "dependent_person_ids": [],
    })

    acct = await _account(client, nancy["id"], "CTO", "2020-01-01")
    instrument_id = await _buy_lot(client, acct["id"], "IE00B4L5Y983", "10", "100", "2025-01-01")
    await _sell_lot(client, acct["id"], instrument_id, "10", "150", "2026-06-01")

    res = await client.get(
        "/api/v1/tax/estimate", params={"year": 2026, "include_investments": True}
    )
    body = res.json()

    assert float(body["investment_income"]["realized_gains_total"]) == 500.0
    assert "single_filing_investment_income_attributed_to_primary" not in body[
        "simplifications_applied"
    ]


async def test_single_filing_attributes_investment_income_to_primary(client: AsyncClient) -> None:
    await _login(client)
    antoine = await _person(client, "Antoine", True)
    await _person(client, "Camille", False)
    await _payslip(client, antoine["id"], "2026-06-01", "60000", "54000", "5000")

    acct = await _account(client, antoine["id"], "CTO", "2020-01-01")
    instrument_id = await _buy_lot(client, acct["id"], "IE00B4L5Y983", "10", "100", "2025-01-01")
    await _sell_lot(client, acct["id"], instrument_id, "10", "150", "2026-06-01")

    res = await client.get(
        "/api/v1/tax/estimate", params={"year": 2026, "include_investments": True}
    )
    body = res.json()

    assert float(body["investment_income"]["realized_gains_total"]) == 500.0
    assert "single_filing_investment_income_attributed_to_primary" in body[
        "simplifications_applied"
    ]


# ── Minor vs. adult dependents (quotient familial parts) ───────────────────


async def test_minor_dependent_gets_progressive_half_part(client: AsyncClient) -> None:
    await _login(client)
    antoine = await _person(client, "Antoine", True)
    await _person(client, "Camille", False)
    child = await _person(client, "Theo", False, date_of_birth="2015-06-01")
    await _payslip(client, antoine["id"], "2026-06-01", "60000", "54000", "5000")
    await client.put("/api/v1/tax/household-settings", json={
        "filing_status": "married_pacs", "dependent_person_ids": [child["id"]],
    })

    res = await client.get("/api/v1/tax/estimate", params={"year": 2026})
    body = res.json()

    assert float(body["parts"]) == 2.5
    assert "adult_dependents_flat_one_part" not in body["simplifications_applied"]
    assert "dependent_age_unknown_assumed_minor" not in body["simplifications_applied"]


async def test_adult_dependent_gets_flat_full_part(client: AsyncClient) -> None:
    await _login(client)
    antoine = await _person(client, "Antoine", True)
    await _person(client, "Camille", False)
    adult_dependent = await _person(client, "Grandma", False, date_of_birth="1950-01-01")
    await _payslip(client, antoine["id"], "2026-06-01", "60000", "54000", "5000")
    await client.put("/api/v1/tax/household-settings", json={
        "filing_status": "married_pacs", "dependent_person_ids": [adult_dependent["id"]],
    })

    res = await client.get("/api/v1/tax/estimate", params={"year": 2026})
    body = res.json()

    # 2 (married base) + 1 flat part for the adult dependent = 3, not 2.5.
    assert float(body["parts"]) == 3.0
    assert "adult_dependents_flat_one_part" in body["simplifications_applied"]


async def test_mixed_minor_and_adult_dependents_combine(client: AsyncClient) -> None:
    await _login(client)
    antoine = await _person(client, "Antoine", True)
    await _person(client, "Camille", False)
    child = await _person(client, "Theo", False, date_of_birth="2015-06-01")
    adult_dependent = await _person(client, "Grandma", False, date_of_birth="1950-01-01")
    await _payslip(client, antoine["id"], "2026-06-01", "60000", "54000", "5000")
    await client.put("/api/v1/tax/household-settings", json={
        "filing_status": "married_pacs",
        "dependent_person_ids": [child["id"], adult_dependent["id"]],
    })

    res = await client.get("/api/v1/tax/estimate", params={"year": 2026})
    body = res.json()

    # 2 (base) + 0.5 (minor) + 1 (adult) = 3.5
    assert float(body["parts"]) == 3.5
    assert "adult_dependents_flat_one_part" in body["simplifications_applied"]


async def test_dependent_without_birth_date_assumed_minor(client: AsyncClient) -> None:
    await _login(client)
    antoine = await _person(client, "Antoine", True)
    await _person(client, "Camille", False)
    child = await _person(client, "Theo", False)  # no date_of_birth
    await _payslip(client, antoine["id"], "2026-06-01", "60000", "54000", "5000")
    await client.put("/api/v1/tax/household-settings", json={
        "filing_status": "married_pacs", "dependent_person_ids": [child["id"]],
    })

    res = await client.get("/api/v1/tax/estimate", params={"year": 2026})
    body = res.json()

    assert float(body["parts"]) == 2.5
    assert "dependent_age_unknown_assumed_minor" in body["simplifications_applied"]


async def test_single_filing_adult_dependent_attributed_to_primary(client: AsyncClient) -> None:
    await _login(client)
    antoine = await _person(client, "Antoine", True)
    await _person(client, "Camille", False)
    adult_dependent = await _person(client, "Grandma", False, date_of_birth="1950-01-01")
    await _payslip(client, antoine["id"], "2026-06-01", "60000", "54000", "5000")
    await client.put("/api/v1/tax/household-settings", json={
        "filing_status": "single", "dependent_person_ids": [adult_dependent["id"]],
    })

    res = await client.get("/api/v1/tax/estimate", params={"year": 2026})
    body = res.json()

    antoine_entry = next(p for p in body["persons"] if p["person_id"] == antoine["id"])
    # 1 (single base) + 1 flat part for the adult dependent = 2, not 1.5.
    assert float(antoine_entry["parts_used"]) == 2.0
