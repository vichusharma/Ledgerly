"""Tax filing domain schemas — Features J1/J2/J3/J5 (docs/Backlog.md)."""
from __future__ import annotations

import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.domains.tax_filing.models import (
    EliminationMethod,
    ForeignIncomeType,
    TaxDocumentType,
)


class PersonTaxResidencyOut(BaseModel):
    person_id: int
    home_country_code: str | None
    home_country_tax_id: str | None
    french_tax_number: str | None
    notes: str | None


class PersonTaxResidencyUpdateIn(BaseModel):
    home_country_code: str | None = None
    home_country_tax_id: str | None = None
    french_tax_number: str | None = None
    notes: str | None = None


class TreatyMetadataOut(BaseModel):
    country_code: str
    country_name: str
    default_elimination_method: EliminationMethod
    treaty_reference: str
    notes: str | None

    model_config = {"from_attributes": True}


class TaxDocumentOut(BaseModel):
    id: int
    person_id: int | None
    tax_year: int | None
    document_type: TaxDocumentType
    original_filename: str
    content_type: str
    related_record_type: str | None
    related_record_id: int | None
    uploaded_at: datetime.datetime

    model_config = {"from_attributes": True}


# -- Feature J2: RSU vesting -------------------------------------------------

class RsuVestingPreviewOut(BaseModel):
    """Best-effort candidate fields from an RSU vest confirmation PDF.
    Every field is nullable and reviewed/corrected by the user before
    anything is saved — no real sample document was available to tune
    these regexes against (built generically, same approach the payslip
    parser started from)."""
    grant_date: datetime.date | None = None
    total_shares: Decimal | None = None
    cliff_months: int | None = None
    vesting_months: int | None = None
    grant_price: Decimal | None = None
    vest_date: datetime.date | None = None
    vested_shares: Decimal | None = None
    vest_fmv: Decimal | None = None


class RsuVestingConfirmIn(BaseModel):
    person_id: int
    account_id: int
    instrument_id: int
    tax_year: int
    grant_date: datetime.date
    total_shares: Decimal
    cliff_months: int = 12
    vesting_months: int = 48
    grant_price: Decimal
    vest_date: datetime.date
    vested_shares: Decimal
    vest_fmv: Decimal


class RsuVestingOut(BaseModel):
    vesting_schedule_id: int
    lot_id: int
    account_id: int
    instrument_id: int
    grant_date: datetime.date
    total_shares: Decimal
    cliff_months: int
    vesting_months: int
    grant_price: Decimal
    vest_date: datetime.date
    vested_shares: Decimal
    vest_fmv: Decimal


# -- Feature J2: ESPP purchases -----------------------------------------------

class EsppPurchasePreviewOut(BaseModel):
    purchase_date: datetime.date | None = None
    shares: Decimal | None = None
    purchase_price: Decimal | None = None
    fmv_at_purchase: Decimal | None = None
    discount_pct: Decimal | None = None


class EsppPurchaseConfirmIn(BaseModel):
    person_id: int
    account_id: int
    instrument_id: int
    tax_year: int
    purchase_date: datetime.date
    shares: Decimal
    purchase_price: Decimal
    fmv_at_purchase: Decimal
    discount_pct: Decimal | None = None


class EsppPurchaseOut(BaseModel):
    lot_id: int
    account_id: int
    instrument_id: int
    purchase_date: datetime.date
    shares: Decimal
    purchase_price: Decimal
    fmv_at_acquisition: Decimal | None
    discount_pct: Decimal | None


# -- Feature J2: foreign income (Form 2047) ----------------------------------

class ForeignIncomePreviewOut(BaseModel):
    source_country_code: str | None = None
    source_description: str | None = None
    gross_amount_eur: Decimal | None = None
    foreign_tax_paid_eur: Decimal | None = None
    income_date: datetime.date | None = None


class ForeignIncomeCreateIn(BaseModel):
    person_id: int
    tax_year: int
    income_type: ForeignIncomeType
    source_country_code: str
    source_description: str
    gross_amount_eur: Decimal
    foreign_tax_paid_eur: Decimal = Decimal("0")
    elimination_method_override: EliminationMethod | None = None
    notes: str | None = None


class ForeignIncomeUpdateIn(BaseModel):
    income_type: ForeignIncomeType | None = None
    source_country_code: str | None = None
    source_description: str | None = None
    gross_amount_eur: Decimal | None = None
    foreign_tax_paid_eur: Decimal | None = None
    elimination_method_override: EliminationMethod | None = None
    notes: str | None = None


class ForeignIncomeOut(BaseModel):
    id: int
    person_id: int
    tax_year: int
    income_type: ForeignIncomeType
    source_country_code: str
    source_description: str
    gross_amount_eur: Decimal
    foreign_tax_paid_eur: Decimal
    elimination_method_override: EliminationMethod | None
    notes: str | None

    model_config = {"from_attributes": True}


# -- Feature J2: foreign accounts (Form 3916) --------------------------------

class ForeignAccountPreviewOut(BaseModel):
    bank_name: str | None = None
    country_code: str | None = None
    account_identifier_masked: str | None = None
    opened_this_year: bool | None = None
    closed_this_year: bool | None = None


class ForeignAccountCreateIn(BaseModel):
    person_id: int
    tax_year: int
    account_id: int | None = None
    bank_name: str
    country_code: str
    account_identifier_masked: str | None = None
    opened_this_year: bool = False
    closed_this_year: bool = False
    notes: str | None = None


class ForeignAccountUpdateIn(BaseModel):
    account_id: int | None = None
    bank_name: str | None = None
    country_code: str | None = None
    account_identifier_masked: str | None = None
    opened_this_year: bool | None = None
    closed_this_year: bool | None = None
    notes: str | None = None


class ForeignAccountOut(BaseModel):
    id: int
    person_id: int
    tax_year: int
    account_id: int | None
    bank_name: str
    country_code: str
    account_identifier_masked: str | None
    opened_this_year: bool
    closed_this_year: bool
    notes: str | None

    model_config = {"from_attributes": True}


# -- Feature J5: FilingSnapshot -----------------------------------------

class BoxEntryOut(BaseModel):
    code: str
    label: str
    amount: Decimal


class ForeignIncomeLineOut(BaseModel):
    source_country_code: str
    source_description: str
    gross_amount_eur: Decimal
    elimination_method: str
    simplification_keys: list[str]
    french_tax_credit_or_exemption: Decimal


class ForeignAccountEntryOut(BaseModel):
    bank_name: str
    country_code: str
    account_identifier_masked: str | None
    opened_this_year: bool
    closed_this_year: bool


class FilingSnapshotPayload(BaseModel):
    year: int
    bareme_tax_year_used: int
    estimated_tax: Decimal
    balance: Decimal
    boxes_2042: list[BoxEntryOut]
    lines_2047: list[ForeignIncomeLineOut]
    entries_3916: list[ForeignAccountEntryOut]
    validation_issues: list[str]
    simplifications_applied: list[str]


class FilingSnapshotOut(BaseModel):
    tax_year: int
    payload: dict
    locked: bool
    computed_at: datetime.datetime
    locked_at: datetime.datetime | None

    model_config = {"from_attributes": True}
