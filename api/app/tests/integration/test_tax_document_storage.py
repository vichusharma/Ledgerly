"""Tests — encrypted document storage crypto helper (Feature J3-S1/S2,
docs/Backlog.md). `TaxFilingService.store_document`/`list_documents`/
`get_document_content`/`delete_document` have no REST endpoints yet
(list/download/delete are Feature J3-S3-S5, built once Feature J2 gives
documents something to attach to) — they get real integration-test
coverage through those endpoints via the standard `client` HTTP
fixture then, matching every other test file in this repo. (The raw
`db_session` fixture used standalone, without going through the `client`
fixture's ASGI transport, hits a genuine Python 3.14/asyncpg/pytest-
asyncio event-loop-scope teardown bug — nothing else in this codebase
exercises a service directly against `db_session` for exactly this
reason, so this file doesn't either.)"""
from __future__ import annotations

import pytest

from app.infra.document_crypto import decrypt_bytes, encrypt_bytes


def test_encrypt_decrypt_roundtrip() -> None:
    original = b"%PDF-1.4 fake rsu vesting statement bytes"
    ciphertext = encrypt_bytes(original)
    assert ciphertext != original
    assert decrypt_bytes(ciphertext) == original


def test_decrypt_garbage_raises_value_error() -> None:
    with pytest.raises(ValueError):
        decrypt_bytes(b"not a real fernet token")
