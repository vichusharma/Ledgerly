"""Pension router — French state pension (régime général + AGIRC-ARRCO) projection."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.domains.pension.schemas import PensionProjectionIn, PensionProjectionOut

router = APIRouter(tags=["pension"], dependencies=[Depends(get_current_user)])


@router.post("/pension/project", response_model=PensionProjectionOut)
async def project_pension(body: PensionProjectionIn) -> PensionProjectionOut:
    """
    Stateless French state pension projection.
    Returns régime général + AGIRC-ARRCO estimates with a sensitivity table
    showing the impact of retiring earlier or later than planned.
    """
    from app.core.pension import project_pension as _compute

    result = _compute(body)
    return PensionProjectionOut.model_validate(result)
