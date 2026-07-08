"""Application-layer document encryption — Feature J3 (docs/Backlog.md).

First real consumer of `Settings.encryption_key`/`ENCRYPTION_KEY_FILE`
(already resolved from a Docker secret in `infra/settings.py`, but with
zero consumers anywhere in the codebase before this). Uses Fernet
(AES-128-CBC + HMAC, via the already-a-dependency `cryptography`
library) instead of adding a new DB extension (`pgcrypto`) — this is
functionally equivalent column-level encryption without a new
dependency, matching `docs/SECURITY.md`'s reserved-for-genuinely-
sensitive-data intent.
"""
from __future__ import annotations

import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.infra.settings import get_settings


@lru_cache
def _fernet() -> Fernet:
    # Fernet requires a 32-byte url-safe base64-encoded key; derive one
    # deterministically from the configured passphrase so the raw
    # ENCRYPTION_KEY_FILE secret can be any length/format.
    digest = hashlib.sha256(get_settings().encryption_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_bytes(data: bytes) -> bytes:
    return _fernet().encrypt(data)


def decrypt_bytes(token: bytes) -> bytes:
    try:
        return _fernet().decrypt(token)
    except InvalidToken as exc:
        raise ValueError(
            "Document could not be decrypted — wrong encryption key or corrupted data"
        ) from exc
