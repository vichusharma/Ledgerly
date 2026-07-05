"""Accounts domain Pydantic schemas."""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field

from app.domains.accounts.models import AccountType, WrapperType


class HouseholdSettingsOut(BaseModel):
    price_lookup_enabled: bool


class HouseholdSettingsUpdateIn(BaseModel):
    price_lookup_enabled: bool


class PersonCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    is_primary: bool = False


class PersonOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    name: str
    is_primary: bool
    household_id: int


class AccountCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: AccountType
    wrapper_type: WrapperType | None = None
    institution: str | None = None
    currency: str = "EUR"
    owner_id: int
    joint_owner_id: int | None = None
    ownership_pct: Decimal = Decimal("100.00")
    notes: str | None = None


class AccountUpdateIn(BaseModel):
    name: str | None = None
    type: AccountType | None = None
    institution: str | None = None
    owner_id: int | None = None
    joint_owner_id: int | None = None
    wrapper_type: WrapperType | None = None
    ownership_pct: Decimal | None = None
    notes: str | None = None


class AccountOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    name: str
    type: AccountType
    wrapper_type: WrapperType | None
    institution: str | None
    currency: str
    owner_id: int
    joint_owner_id: int | None
    ownership_pct: Decimal
    is_archived: bool
    notes: str | None
