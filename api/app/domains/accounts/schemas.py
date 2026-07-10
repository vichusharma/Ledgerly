"""Accounts domain Pydantic schemas."""
from __future__ import annotations

import datetime
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
    date_of_birth: datetime.date | None = None


class PersonUpdateIn(BaseModel):
    name: str | None = None
    is_primary: bool | None = None
    date_of_birth: datetime.date | None = None


class PersonOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    name: str
    is_primary: bool
    household_id: int
    date_of_birth: datetime.date | None


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
    opened_at: datetime.date | None = None
    country_code: str | None = None
    manual_balance: Decimal | None = None


class AccountUpdateIn(BaseModel):
    name: str | None = None
    type: AccountType | None = None
    institution: str | None = None
    owner_id: int | None = None
    joint_owner_id: int | None = None
    wrapper_type: WrapperType | None = None
    ownership_pct: Decimal | None = None
    notes: str | None = None
    opened_at: datetime.date | None = None
    country_code: str | None = None
    manual_balance: Decimal | None = None


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
    opened_at: datetime.date | None
    country_code: str | None
    manual_balance: Decimal | None
