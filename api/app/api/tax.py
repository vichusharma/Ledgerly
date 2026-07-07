"""Tax profile router — Feature I2 of docs/Backlog.md (facts only, no
tax computation yet)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.domains.tax.schemas import (
    HouseholdTaxSettingsOut,
    HouseholdTaxSettingsUpdateIn,
    PersonTaxProfileOut,
    PersonTaxProfileUpdateIn,
    TaxEstimateOut,
)
from app.domains.tax.service import TaxService

router = APIRouter(tags=["tax"], dependencies=[Depends(get_current_user)])


@router.get("/tax/profile/{person_id}", response_model=PersonTaxProfileOut)
async def get_person_tax_profile(
    person_id: int, db: AsyncSession = Depends(get_db)
) -> PersonTaxProfileOut:
    profile = await TaxService(db).get_person_tax_profile(person_id)
    if profile is None:
        raise HTTPException(404, "Person not found")
    return profile


@router.put("/tax/profile/{person_id}", response_model=PersonTaxProfileOut)
async def set_person_tax_profile(
    person_id: int, body: PersonTaxProfileUpdateIn, db: AsyncSession = Depends(get_db)
) -> PersonTaxProfileOut:
    profile = await TaxService(db).set_person_tax_profile(person_id, body)
    if profile is None:
        raise HTTPException(404, "Person not found")
    return profile


@router.get("/tax/household-settings", response_model=HouseholdTaxSettingsOut)
async def get_household_tax_settings(
    db: AsyncSession = Depends(get_db),
) -> HouseholdTaxSettingsOut:
    return await TaxService(db).get_household_tax_settings()


@router.put("/tax/household-settings", response_model=HouseholdTaxSettingsOut)
async def set_household_tax_settings(
    body: HouseholdTaxSettingsUpdateIn, db: AsyncSession = Depends(get_db)
) -> HouseholdTaxSettingsOut:
    try:
        return await TaxService(db).set_household_tax_settings(body)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/tax/estimate", response_model=TaxEstimateOut)
async def get_tax_estimate(
    year: int,
    include_investments: bool = False,
    db: AsyncSession = Depends(get_db),
) -> TaxEstimateOut:
    """Stateless salary-only tax estimate for `year`. `include_investments`
    is accepted for forward-compatibility but has no effect yet (Feature I4)."""
    try:
        return await TaxService(db).get_tax_estimate(year, include_investments)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
