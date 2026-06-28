"""GDPR export & erase router (P2)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.domains.planning.service import PlanningService

router = APIRouter(tags=["gdpr"], dependencies=[Depends(get_current_user)])


@router.get("/export")
async def export_data(db: AsyncSession = Depends(get_db)) -> StreamingResponse:
    """GDPR full export — returns a ZIP of all user data as JSON/CSV."""
    zip_bytes = await PlanningService(db).export_all_data()
    return StreamingResponse(
        iter([zip_bytes]),
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="ledgerly_export.zip"'},
    )


@router.delete("/account/data", status_code=204)
async def erase_data(db: AsyncSession = Depends(get_db)) -> None:
    """GDPR hard erase — deletes all personal financial data."""
    await PlanningService(db).erase_all_data()
