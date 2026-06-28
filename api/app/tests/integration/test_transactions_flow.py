"""Integration tests — CSV import, dedup, categorization, split."""
from __future__ import annotations

import io
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

PASSWORD = "S3cur3P@ss!"

SAMPLE_CSV = """\
date,description,amount
2024-01-15,Carrefour Market,-42.50
2024-01-16,Virement salaire,3200.00
2024-01-17,EDF facture,-89.30
"""


async def _setup_and_login(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/setup", json={"password": PASSWORD})
    await client.post("/api/v1/auth/login", json={"password": PASSWORD})


async def _create_account(client: AsyncClient) -> dict:
    person = (await client.post("/api/v1/persons", json={"name": "Antoine", "is_primary": True})).json()
    acct = (await client.post("/api/v1/accounts", json={
        "name": "Compte courant", "type": "bank", "owner_id": person["id"],
    })).json()
    return acct


async def test_manual_transaction(client: AsyncClient) -> None:
    await _setup_and_login(client)
    acct = await _create_account(client)
    res = await client.post("/api/v1/transactions", json={
        "account_id": acct["id"],
        "date": "2024-01-20",
        "description": "Test dépense",
        "amount": "-50.00",
    })
    assert res.status_code == 201
    assert res.json()["description"] == "Test dépense"


async def test_csv_import_dedup(client: AsyncClient) -> None:
    await _setup_and_login(client)
    acct = await _create_account(client)

    # Create a simple mapping
    mapping = (await client.post("/api/v1/import/mappings", json={
        "institution": "TestBank",
        "column_map": {"date": "date", "description": "description", "amount": "amount"},
        "date_format": "%Y-%m-%d",
        "decimal_separator": ".",
        "encoding": "utf-8",
        "skip_rows": 0,
    })).json()

    file_bytes = SAMPLE_CSV.encode("utf-8")

    # First import
    res1 = await client.post(
        "/api/v1/imports/csv",
        files={"file": ("test.csv", io.BytesIO(file_bytes), "text/csv")},
        data={"account_id": str(acct["id"]), "mapping_id": str(mapping["id"])},
    )
    assert res1.status_code == 201
    batch1 = res1.json()
    assert batch1["imported"] == 3
    assert batch1["duplicates"] == 0

    # Second import — all duplicates
    res2 = await client.post(
        "/api/v1/imports/csv",
        files={"file": ("test.csv", io.BytesIO(file_bytes), "text/csv")},
        data={"account_id": str(acct["id"]), "mapping_id": str(mapping["id"])},
    )
    assert res2.status_code == 201
    batch2 = res2.json()
    assert batch2["imported"] == 0
    assert batch2["duplicates"] == 3


async def test_rollback_batch(client: AsyncClient) -> None:
    await _setup_and_login(client)
    acct = await _create_account(client)
    mapping = (await client.post("/api/v1/import/mappings", json={
        "institution": "RollbackBank",
        "column_map": {"date": "date", "description": "description", "amount": "amount"},
        "date_format": "%Y-%m-%d",
        "decimal_separator": ".",
        "encoding": "utf-8",
        "skip_rows": 0,
    })).json()
    file_bytes = SAMPLE_CSV.encode("utf-8")
    batch = (await client.post(
        "/api/v1/imports/csv",
        files={"file": ("test.csv", io.BytesIO(file_bytes), "text/csv")},
        data={"account_id": str(acct["id"]), "mapping_id": str(mapping["id"])},
    )).json()

    # Rollback
    res = await client.delete(f"/api/v1/imports/{batch['batch_id']}")
    assert res.status_code in (200, 204)

    # Transactions should be gone
    txns = await client.get(f"/api/v1/transactions?account_id={acct['id']}")
    assert len(txns.json()) == 0
