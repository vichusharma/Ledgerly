"""Integration tests — generate-pdf endpoint (Feature J6, docs/Backlog.md),
end to end from a computed FilingSnapshot through to real PDF/zip bytes."""
from __future__ import annotations

import io
import zipfile

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


async def test_generate_pdf_before_compute_404s(client: AsyncClient) -> None:
    await _person(client)
    res = await client.post(
        "/api/v1/tax-filing/generate-pdf", params={"year": 2026, "form": "2042"}
    )
    assert res.status_code == 404


async def test_generate_single_form_pdf(client: AsyncClient) -> None:
    await _person(client)
    await client.post("/api/v1/tax-filing/compute", params={"year": 2026})

    res = await client.post(
        "/api/v1/tax-filing/generate-pdf", params={"year": 2026, "form": "2042"}
    )
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert res.content.startswith(b"%PDF")


async def test_generate_all_returns_zip_bundle(client: AsyncClient) -> None:
    await _person(client)
    await client.post("/api/v1/tax-filing/compute", params={"year": 2026})

    res = await client.post(
        "/api/v1/tax-filing/generate-pdf", params={"year": 2026, "form": "all"}
    )
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/zip"
    zf = zipfile.ZipFile(io.BytesIO(res.content))
    names = zf.namelist()
    assert "2042_2026.pdf" in names
    assert "2047_2026.pdf" in names
    assert "3916_2026.pdf" in names
    for name in names:
        assert zf.read(name).startswith(b"%PDF")


async def test_generate_pdf_with_lock_true_locks_the_snapshot(client: AsyncClient) -> None:
    await _person(client)
    await client.post("/api/v1/tax-filing/compute", params={"year": 2026})

    res = await client.post(
        "/api/v1/tax-filing/generate-pdf",
        params={"year": 2026, "form": "2042", "lock": True},
    )
    assert res.status_code == 200

    snapshot = (await client.get("/api/v1/tax-filing/forms/2026")).json()
    assert snapshot["locked"] is True

    recompute = await client.post("/api/v1/tax-filing/compute", params={"year": 2026})
    assert recompute.status_code == 409


async def test_generate_pdf_unknown_form_400s(client: AsyncClient) -> None:
    await _person(client)
    await client.post("/api/v1/tax-filing/compute", params={"year": 2026})
    res = await client.post(
        "/api/v1/tax-filing/generate-pdf", params={"year": 2026, "form": "9999"}
    )
    assert res.status_code == 400
