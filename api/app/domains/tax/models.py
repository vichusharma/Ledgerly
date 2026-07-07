"""Tax domain models — household filing status and explicit dependents list.

Per-person impatriate-regime columns live on `Person` itself
(`app.domains.accounts.models`) since eligibility is a fact about an
individual, not the household. Filing status and dependents are
household-wide facts, so they live here instead. See Feature I2 in
docs/Backlog.md.
"""
from __future__ import annotations

import datetime
import enum
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db import Base


class FilingStatus(str, enum.Enum):
    single = "single"
    married_pacs = "married_pacs"


class HouseholdTaxSettings(Base):
    __tablename__ = "household_tax_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    household_id: Mapped[int] = mapped_column(
        ForeignKey("households.id"), nullable=False, unique=True
    )
    filing_status: Mapped[FilingStatus] = mapped_column(
        String(20), nullable=False, default=FilingStatus.single
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class HouseholdTaxDependent(Base):
    """An explicit opt-in: this Person counts as a dependent for quotient
    familial purposes. Never auto-inferred from age/relationship."""

    __tablename__ = "household_tax_dependents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    household_tax_settings_id: Mapped[int] = mapped_column(
        ForeignKey("household_tax_settings.id"), nullable=False
    )
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "household_tax_settings_id", "person_id", name="uq_tax_dependent_settings_person"
        ),
    )


class TaxYearConfig(Base):
    """Barème progressif + quotient-familial plafonnement for one tax year.

    The barème changes every year via Loi de Finances — this table makes
    updating it a data migration, not a code change. `brackets` is a list
    of `{"up_to": float|None, "rate": float}` ordered ascending, last
    entry `up_to=null` (no upper bound). See migration
    `0010_tax_year_config.py` for the seeded placeholder figures and why
    they're a placeholder.
    """

    __tablename__ = "tax_year_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tax_year: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    brackets: Mapped[list] = mapped_column(JSONB, nullable=False)
    quotient_familial_plafond_per_half_part: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
