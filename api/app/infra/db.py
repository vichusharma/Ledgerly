"""SQLAlchemy async engine + session factory."""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.infra.settings import get_settings


class Base(DeclarativeBase):
    """Shared declarative base for all SQLAlchemy models."""


_engine: object = None
async_session_factory: async_sessionmaker[AsyncSession]


def _build_engine() -> None:
    global _engine, async_session_factory
    settings = get_settings()
    _engine = create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=not settings.is_production,
    )
    async_session_factory = async_sessionmaker(
        bind=_engine,  # type: ignore[arg-type]
        expire_on_commit=False,
        autoflush=False,
    )


_build_engine()


async def init_db() -> None:
    """Create all tables (used in tests / seed; prod uses Alembic)."""
    from sqlalchemy.ext.asyncio import AsyncEngine

    assert isinstance(_engine, AsyncEngine)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields an async DB session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
