"""FastAPI application factory."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.infra.scheduler import start_scheduler, stop_scheduler
from app.infra.settings import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    logger.info("Starting Ledgerly API…")
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()
    logger.info("Ledgerly API stopped.")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Ledgerly API",
        version="0.1.0",
        description="Local-first personal finance decision platform for French households.",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # CORS — only allow same origin in production
    origins = ["https://localhost", "https://127.0.0.1"]
    if not settings.is_production:
        origins += ["http://localhost:3000", "http://127.0.0.1:3000"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    from app.api.auth import router as auth_router
    from app.api.accounts import router as accounts_router
    from app.api.transactions import router as transactions_router
    from app.api.imports import router as imports_router
    from app.api.investments import router as investments_router
    from app.api.liabilities import router as liabilities_router
    from app.api.networth import router as networth_router
    from app.api.scenarios import router as scenarios_router
    from app.api.planning import router as planning_router
    from app.api.export import router as export_router

    prefix = "/api/v1"
    app.include_router(auth_router, prefix=prefix)
    app.include_router(accounts_router, prefix=prefix)
    app.include_router(transactions_router, prefix=prefix)
    app.include_router(imports_router, prefix=prefix)
    app.include_router(investments_router, prefix=prefix)
    app.include_router(liabilities_router, prefix=prefix)
    app.include_router(networth_router, prefix=prefix)
    app.include_router(scenarios_router, prefix=prefix)
    app.include_router(planning_router, prefix=prefix)
    app.include_router(export_router, prefix=prefix)

    @app.get("/health", tags=["ops"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
