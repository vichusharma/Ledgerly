"""Net worth router — current + time series + manual snapshot trigger."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.domains.networth.schemas import NetWorthOut, NetWorthSeriesOut
from app.domains.networth.service import NetWorthService

router = APIRouter(tags=["networth"], dependencies=[Depends(get_current_user)])


@router.get("/networth", response_model=NetWorthOut)
async def get_networth(
    scope: str = "household",
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> NetWorthOut:
    return await NetWorthService(db).get_networth(
        scope=scope, from_date=from_date, to_date=to_date
    )


@router.get("/networth/series", response_model=list[NetWorthSeriesOut])
async def get_networth_series(
    scope: str = "household",
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[NetWorthSeriesOut]:
    return await NetWorthService(db).get_series(
        scope=scope, from_date=from_date, to_date=to_date
    )


@router.post("/networth/snapshot", status_code=204)
async def trigger_snapshot(db: AsyncSession = Depends(get_db)) -> None:
    """Manually trigger a net-worth snapshot (month-end freeze)."""
    await NetWorthService(db).take_snapshot()
