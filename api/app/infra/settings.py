"""Application settings loaded from environment variables + Docker secret files."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _read_secret(path: str | None) -> str | None:
    """Read a Docker secret from a file path."""
    if path and Path(path).exists():
        return Path(path).read_text().strip()
    return None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://ledgerly:ledgerly@localhost:5432/ledgerly"
    )
    db_password_file: str | None = None

    # Auth
    secret_key_file: str | None = None
    secret_key: str = Field(default="")  # resolved below

    # Encryption
    encryption_key_file: str | None = None
    encryption_key: str = Field(default="")  # resolved below

    # App
    environment: str = Field(default="development")
    access_token_expire_minutes: int = 60 * 8  # 8 hours

    # Optional price provider (Phase 3)
    price_provider_url: str | None = None
    price_provider_api_key_file: str | None = None

    @field_validator("secret_key", mode="before")
    @classmethod
    def resolve_secret_key(cls, v: str, info: object) -> str:  # type: ignore[override]
        data = info.data if hasattr(info, "data") else {}
        from_file = _read_secret(data.get("secret_key_file") or os.environ.get("SECRET_KEY_FILE"))
        return from_file or v or "dev-insecure-secret-change-me"

    @field_validator("encryption_key", mode="before")
    @classmethod
    def resolve_encryption_key(cls, v: str, info: object) -> str:  # type: ignore[override]
        data = info.data if hasattr(info, "data") else {}
        from_file = _read_secret(
            data.get("encryption_key_file") or os.environ.get("ENCRYPTION_KEY_FILE")
        )
        return from_file or v or "dev-insecure-enc-key-change-me!"

    @model_validator(mode="after")
    def resolve_db_password(self) -> "Settings":
        file_path = self.db_password_file or os.environ.get("DB_PASSWORD_FILE")
        password = _read_secret(file_path)
        if password:
            parsed = urlparse(self.database_url)
            netloc = f"{parsed.username}:{password}@{parsed.hostname}:{parsed.port}"
            self.database_url = urlunparse(parsed._replace(netloc=netloc))
        return self

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
