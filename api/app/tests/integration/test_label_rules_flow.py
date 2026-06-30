"""Integration tests — bulk labels + on-ingest auto-labeling."""
from __future__ import annotations

import io

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

PASSWORD = "S3cur3P@ss!"

SAMPLE_CSV = """\
date,description,amount
2024-01-15,CB CARREFOUR MARKET 12/05 PARIS,-42.50
2024-01-16,VIR SALAIRE,3200.00
2024-01-17,PRLV EDF FACTURE,-89.30
"""


async def _setup_and_login(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/setup", json={"password": PASSWORD})
    await client.post("/api/v1/auth/login", json={"password": PASSWORD})


async def _create_account(client: AsyncClient) -> dict:
    person = (await client.post("/api/v1/persons", json={"name": "Antoine", "is_primary": True})).json()
    return (await client.post("/api/v1/accounts", json={
        "name": "Compte courant", "type": "bank", "owner_id": person["id"],
    })).json()


async def test_bulk_labels_and_label_rules_roundtrip(client: AsyncClient) -> None:
    await _setup_and_login(client)

    # Bulk-create labels with multiple independent patterns each (OR-matched,
    # not a single comma-joined string — that was the original bug).
    res = await client.post("/api/v1/labels/bulk", json={"labels": [
        {"name": "Groceries", "color": "#22c55e", "patterns": ["CARREFOUR", "MONOPRIX"]},
        {"name": "Income", "color": "#3b82f6", "patterns": ["SALAIRE"]},
        {"name": "Misc", "color": "#6b7280", "patterns": []},  # no patterns → no rules
    ]})
    assert res.status_code == 200
    names = {lb["name"] for lb in res.json()}
    assert names == {"Groceries", "Income", "Misc"}

    # Three rules total: two for Groceries (one per pattern), one for Income.
    rules = (await client.get("/api/v1/label-rules")).json()
    assert len(rules) == 3
    patterns = {r["pattern"] for r in rules}
    assert patterns == {"CARREFOUR", "MONOPRIX", "SALAIRE"}

    # Re-running bulk replaces this label's rules rather than duplicating them.
    res2 = await client.post("/api/v1/labels/bulk", json={"labels": [
        {"name": "Groceries", "color": "#22c55e", "patterns": ["CARREFOUR"]},
    ]})
    assert res2.status_code == 200
    rules2 = (await client.get("/api/v1/label-rules")).json()
    grocery_id = next(lb["id"] for lb in res.json() if lb["name"] == "Groceries")
    grocery_rules = [r for r in rules2 if r["label_id"] == grocery_id]
    assert len(grocery_rules) == 1
    assert grocery_rules[0]["pattern"] == "CARREFOUR"


async def test_multiple_patterns_on_one_label_match_independently(client: AsyncClient) -> None:
    """A label with several keyword patterns matches if ANY of them appears —
    this is the fix for comma-joined single patterns silently matching nothing."""
    await _setup_and_login(client)
    acct = await _create_account(client)

    await client.post("/api/v1/labels/bulk", json={"labels": [
        {"name": "Eatingout", "color": "#ec4899", "patterns": ["CHICKEN", "TRAMPO"]},
    ]})

    mapping = (await client.post("/api/v1/import/mappings", json={
        "institution": "MultiPatternBank",
        "column_map": {"date": "date", "description": "description", "amount": "amount"},
        "date_format": "%Y-%m-%d",
        "decimal_separator": ".",
        "encoding": "utf-8",
        "skip_rows": 0,
    })).json()
    csv = (
        "date,description,amount\n"
        "2024-02-01,CB CHICKEN SHOP,-12.00\n"
        "2024-02-02,CB TRAMPO RESTO,-30.00\n"
        "2024-02-03,CB UNRELATED MERCHANT,-5.00\n"
    )
    res = await client.post(
        "/api/v1/imports/csv",
        files={"file": ("test.csv", io.BytesIO(csv.encode()), "text/csv")},
        data={"account_id": str(acct["id"]), "mapping_id": str(mapping["id"])},
    )
    assert res.status_code == 201

    txns = (await client.get(f"/api/v1/transactions?account_id={acct['id']}")).json()
    by_desc = {t["description"]: [lb["name"] for lb in t["labels"]] for t in txns}
    assert by_desc["CB CHICKEN SHOP"] == ["Eatingout"]
    assert by_desc["CB TRAMPO RESTO"] == ["Eatingout"]
    assert by_desc["CB UNRELATED MERCHANT"] == []


async def test_labels_applied_on_import(client: AsyncClient) -> None:
    await _setup_and_login(client)
    acct = await _create_account(client)

    await client.post("/api/v1/labels/bulk", json={"labels": [
        {"name": "Groceries", "color": "#22c55e", "patterns": ["CARREFOUR"]},
        {"name": "Income", "color": "#3b82f6", "patterns": ["SALAIRE"]},
    ]})

    mapping = (await client.post("/api/v1/import/mappings", json={
        "institution": "LabelBank",
        "column_map": {"date": "date", "description": "description", "amount": "amount"},
        "date_format": "%Y-%m-%d",
        "decimal_separator": ".",
        "encoding": "utf-8",
        "skip_rows": 0,
    })).json()

    res = await client.post(
        "/api/v1/imports/csv",
        files={"file": ("test.csv", io.BytesIO(SAMPLE_CSV.encode()), "text/csv")},
        data={"account_id": str(acct["id"]), "mapping_id": str(mapping["id"])},
    )
    assert res.status_code == 201
    assert res.json()["row_count"] == 3

    txns = (await client.get(f"/api/v1/transactions?account_id={acct['id']}")).json()
    by_desc = {t["description"]: [lb["name"] for lb in t["labels"]] for t in txns}

    assert by_desc["CB CARREFOUR MARKET 12/05 PARIS"] == ["Groceries"]
    assert by_desc["VIR SALAIRE"] == ["Income"]
    assert by_desc["PRLV EDF FACTURE"] == []


async def test_invalid_pattern_rejected(client: AsyncClient) -> None:
    await _setup_and_login(client)
    label = (await client.post("/api/v1/labels", json={"name": "Bad", "color": "#000000"})).json()
    res = await client.post("/api/v1/label-rules", json={
        "pattern": "[unclosed", "label_id": label["id"],
    })
    assert res.status_code == 422


async def test_rerun_rules_labels_existing_history_without_clobbering_edits(
    client: AsyncClient,
) -> None:
    await _setup_and_login(client)
    acct = await _create_account(client)

    # Import BEFORE any rules exist — nothing gets auto-labeled.
    mapping = (await client.post("/api/v1/import/mappings", json={
        "institution": "RerunBank",
        "column_map": {"date": "date", "description": "description", "amount": "amount"},
        "date_format": "%Y-%m-%d",
        "decimal_separator": ".",
        "encoding": "utf-8",
        "skip_rows": 0,
    })).json()
    await client.post(
        "/api/v1/imports/csv",
        files={"file": ("test.csv", io.BytesIO(SAMPLE_CSV.encode()), "text/csv")},
        data={"account_id": str(acct["id"]), "mapping_id": str(mapping["id"])},
    )
    txns = (await client.get(f"/api/v1/transactions?account_id={acct['id']}")).json()
    assert all(t["labels"] == [] for t in txns)

    # Manually label the EDF transaction — this must survive the re-run.
    edf = next(t for t in txns if "EDF" in t["description"])
    manual_label = (await client.post("/api/v1/labels", json={"name": "Bills", "color": "#000000"})).json()
    await client.put(f"/api/v1/transactions/{edf['id']}/labels", json={"label_ids": [manual_label["id"]]})

    # Now define rules retroactively.
    await client.post("/api/v1/labels/bulk", json={"labels": [
        {"name": "Groceries", "color": "#22c55e", "patterns": ["CARREFOUR"]},
        {"name": "Income", "color": "#3b82f6", "patterns": ["SALAIRE"]},
    ]})

    res = await client.post("/api/v1/transactions/rerun-rules")
    assert res.status_code == 200
    body = res.json()
    assert body["scanned"] >= 3
    assert body["labeled"] == 2  # Carrefour + Salaire rows newly matched

    txns2 = (await client.get(f"/api/v1/transactions?account_id={acct['id']}")).json()
    by_desc = {t["description"]: {lb["name"] for lb in t["labels"]} for t in txns2}
    assert by_desc["CB CARREFOUR MARKET 12/05 PARIS"] == {"Groceries"}
    assert by_desc["VIR SALAIRE"] == {"Income"}
    # The manually-applied label on EDF is preserved (not overwritten).
    assert by_desc["PRLV EDF FACTURE"] == {"Bills"}
