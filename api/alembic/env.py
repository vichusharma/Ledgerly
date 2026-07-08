"""Alembic migration environment — async SQLAlchemy."""
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

# Import all models so Alembic can detect them
from app.infra.db import Base
import app.domains.accounts.models  # noqa: F401
import app.domains.transactions.models  # noqa: F401
import app.domains.imports.models  # noqa: F401
import app.domains.investments.models  # noqa: F401
import app.domains.liabilities.models  # noqa: F401
import app.domains.networth.models  # noqa: F401
import app.domains.scenarios.models  # noqa: F401
import app.domains.planning.models  # noqa: F401
import app.domains.salary.models  # noqa: F401
import app.domains.tax.models  # noqa: F401
import app.domains.tax_filing.models  # noqa: F401
from app.infra.settings import get_settings

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    settings = get_settings()
    context.configure(
        url=settings.database_url.replace("+asyncpg", ""),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):  # type: ignore[no-untyped-def]
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
