"""Accounts & persons router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.domains.accounts.schemas import (
    AccountCreateIn, AccountOut, AccountUpdateIn,
    HouseholdSettingsOut, HouseholdSettingsUpdateIn,
    PersonCreateIn, PersonOut,
)
from app.domains.accounts.service import AccountService

router = APIRouter(tags=["accounts"], dependencies=[Depends(get_current_user)])


# ── Household settings ──────────────────────────────────────────────────────

@router.get("/settings/price-lookup", response_model=HouseholdSettingsOut)
async def get_price_lookup_setting(db: AsyncSession = Depends(get_db)) -> HouseholdSettingsOut:
    return await AccountService(db).get_household_settings()


@router.put("/settings/price-lookup", response_model=HouseholdSettingsOut)
async def set_price_lookup_setting(
    body: HouseholdSettingsUpdateIn, db: AsyncSession = Depends(get_db)
) -> HouseholdSettingsOut:
    return await AccountService(db).update_household_settings(body)


# ── Persons ──────────────────────────────────────────────────────────────────

@router.get("/persons", response_model=list[PersonOut])
async def list_persons(db: AsyncSession = Depends(get_db)) -> list[PersonOut]:
    return await AccountService(db).list_persons()


@router.post("/persons", response_model=PersonOut, status_code=201)
async def create_person(body: PersonCreateIn, db: AsyncSession = Depends(get_db)) -> PersonOut:
    return await AccountService(db).create_person(body)


# ── Accounts ─────────────────────────────────────────────────────────────────

@router.get("/accounts", response_model=list[AccountOut])
async def list_accounts(
    scope: str = "household",
    include_archived: bool = False,
    db: AsyncSession = Depends(get_db),
) -> list[AccountOut]:
    return await AccountService(db).list_accounts(scope=scope, include_archived=include_archived)


@router.post("/accounts", response_model=AccountOut, status_code=201)
async def create_account(body: AccountCreateIn, db: AsyncSession = Depends(get_db)) -> AccountOut:
    return await AccountService(db).create_account(body)


@router.get("/accounts/{account_id}", response_model=AccountOut)
async def get_account(account_id: int, db: AsyncSession = Depends(get_db)) -> AccountOut:
    obj = await AccountService(db).get_account(account_id)
    if obj is None:
        raise HTTPException(404, "Account not found")
    return obj


@router.patch("/accounts/{account_id}", response_model=AccountOut)
async def update_account(
    account_id: int, body: AccountUpdateIn, db: AsyncSession = Depends(get_db)
) -> AccountOut:
    obj = await AccountService(db).update_account(account_id, body)
    if obj is None:
        raise HTTPException(404, "Account not found")
    return obj


@router.delete("/accounts/{account_id}/archive", status_code=204)
async def archive_account(account_id: int, db: AsyncSession = Depends(get_db)) -> None:
    await AccountService(db).archive_account(account_id)
