"""Tax filing domain models — Epic J (docs/Backlog.md).

Sibling to the `tax` domain (Epic I's estimate/profile domain): this
domain adds the facts and forms needed to actually *file*, for a
foreigner who is a French tax resident (matches the household's existing
impatriate-regime setup) — Forms 2042/2047/3916. `tax_filing` calls into
`TaxService`/`core/tax.py` rather than duplicating quotient-familial or
PFU math.

Feature J1 only (this file): per-person residency facts + a seeded
treaty-metadata reference table. Later features (J2-J8) add foreign
income/account declarations, encrypted document storage, the
`tax_filing_rules` engine, and PDF generation — see docs/Backlog.md.
"""
from __future__ import annotations

import datetime
import enum
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db import Base


class EliminationMethod(str, enum.Enum):
    """How a double-taxation treaty eliminates French tax on foreign
    income. See `core/tax_filing_rules.py` (Feature J4) for the actual
    computation of each method."""
    credit_equal_to_french_tax = "credit_equal_to_french_tax"
    exemption_with_effective_rate = "exemption_with_effective_rate"


class PersonTaxResidency(Base):
    """Per-person tax-residency facts. Kept on its own table (not more
    `Person` columns) since it's cohesive to the filing domain rather
    than a universal identity fact — same reasoning `HouseholdTaxSettings`
    lives in `tax`, not on `Household`. Still per-person, not
    household-wide, matching the impatriate-regime convention."""

    __tablename__ = "person_tax_residency"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    person_id: Mapped[int] = mapped_column(
        ForeignKey("persons.id"), nullable=False, unique=True
    )
    home_country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    home_country_tax_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    french_tax_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class TreatyMetadata(Base):
    """Seeded reference data for a handful of countries only (see
    migration 0013_treaty_metadata.py) — not all ~120 French tax
    treaties. Any country not seeded here falls back to the credit
    method with a disclosed `treaty_method_defaulted_unseeded_country`
    simplification flag (Feature J4)."""

    __tablename__ = "treaty_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False, unique=True)
    country_name: Mapped[str] = mapped_column(String(100), nullable=False)
    default_elimination_method: Mapped[EliminationMethod] = mapped_column(
        String(40), nullable=False
    )
    treaty_reference: Mapped[str] = mapped_column(String(200), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class TaxDocumentType(str, enum.Enum):
    """What kind of source document this is — drives which J2 parser/
    declaration table it's associated with. `other` covers anything
    uploaded via the manual-entry paths that still has a document."""
    rsu_vesting = "rsu_vesting"
    espp_purchase = "espp_purchase"
    foreign_dividend = "foreign_dividend"
    foreign_bank_statement = "foreign_bank_statement"
    other = "other"


class TaxDocument(Base):
    """Encrypted original-source-document audit trail (Feature J3) — the
    confirmed scope decision to *retain* RSU/ESPP/foreign-statement
    source PDFs, unlike every other parser in this app (payslips, PDF
    valuations, bank statements), which parses transiently and discards
    the bytes. Built ahead of Feature J2 (per the backlog's delivery
    order) since J2's confirm flows depend on this table existing.

    `related_record_type`/`related_record_id` is a loose, generic
    pointer (not an FK) to whichever J2 record the document ends up
    backing — kept generic rather than one nullable FK column per J2
    table, since a document can be uploaded and reviewed before the
    record it's confirmed into exists yet, and J2 adds several
    unrelated declaration tables (RSU/ESPP/foreign-income/foreign-
    account), not one.
    """

    __tablename__ = "tax_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    person_id: Mapped[int | None] = mapped_column(ForeignKey("persons.id"), nullable=True)
    tax_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    document_type: Mapped[TaxDocumentType] = mapped_column(String(30), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    encrypted_content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    related_record_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    related_record_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    uploaded_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ForeignIncomeType(str, enum.Enum):
    """Form 2047 income categories this module models. `other` covers
    anything not in the specific categories below (still declarable,
    just not distinguished by type for elimination-method purposes)."""
    foreign_dividend = "foreign_dividend"
    foreign_interest = "foreign_interest"
    foreign_salary = "foreign_salary"
    foreign_capital_gain = "foreign_capital_gain"
    other = "other"


class ForeignIncomeDeclaration(Base):
    """Feature J2 — one line of foreign-source income for Form 2047.
    Per-person, per-tax-year; `elimination_method_override` lets a
    specific line diverge from `TreatyMetadata`'s per-country default
    (Feature J4-S3's per-line resolution order: override → treaty
    default → credit-method fallback)."""

    __tablename__ = "foreign_income_declarations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id"), nullable=False)
    tax_year: Mapped[int] = mapped_column(Integer, nullable=False)
    income_type: Mapped[ForeignIncomeType] = mapped_column(String(30), nullable=False)
    source_country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    source_description: Mapped[str] = mapped_column(String(200), nullable=False)
    gross_amount_eur: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    foreign_tax_paid_eur: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), nullable=False, default=Decimal("0")
    )
    elimination_method_override: Mapped[EliminationMethod | None] = mapped_column(
        String(40), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ForeignAccountDeclaration(Base):
    """Feature J2 — one Form 3916 foreign bank/financial account line
    per person per tax year. `account_id` optionally links to an
    existing Ledgerly `Account` when the household also tracks balances
    for it (via `Account.country_code`, Feature J2-S6); many 3916 lines
    won't have one (e.g. a dormant childhood bank account back home
    that's declared but never imported into Ledgerly)."""

    __tablename__ = "foreign_account_declarations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id"), nullable=False)
    tax_year: Mapped[int] = mapped_column(Integer, nullable=False)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    bank_name: Mapped[str] = mapped_column(String(200), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    account_identifier_masked: Mapped[str | None] = mapped_column(String(50), nullable=True)
    opened_this_year: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    closed_this_year: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class FilingSnapshot(Base):
    """Feature J5 — a lockable, stable per-year filing result, built on
    top of Epic I's estimate + Feature J4's `tax_filing_rules` mapping.
    Unlike `/tax/estimate` (deliberately always recomputed fresh),
    a snapshot is a point-in-time JSONB payload the user can lock once
    satisfied with it — recomputing a locked year is rejected (409),
    it must be explicitly unlocked first."""

    __tablename__ = "filing_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tax_year: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    computed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    locked_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
