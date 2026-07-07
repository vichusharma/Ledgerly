"""Tax domain schemas."""
from __future__ import annotations

import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.domains.accounts.models import ImpatriateElectionMethod
from app.domains.tax.models import FilingStatus


class PersonTaxProfileOut(BaseModel):
    person_id: int
    impatriate_enabled: bool
    impatriate_arrival_date: datetime.date | None
    impatriate_election_method: ImpatriateElectionMethod | None


class PersonTaxProfileUpdateIn(BaseModel):
    impatriate_enabled: bool
    impatriate_arrival_date: datetime.date | None = None
    impatriate_election_method: ImpatriateElectionMethod | None = None


class HouseholdTaxSettingsOut(BaseModel):
    filing_status: FilingStatus
    dependent_person_ids: list[int]


class HouseholdTaxSettingsUpdateIn(BaseModel):
    filing_status: FilingStatus
    dependent_person_ids: list[int] = []


class PersonTaxEstimateOut(BaseModel):
    person_id: int
    name: str
    has_payslip_data: bool
    as_of_month: int | None
    gross_annual_projected: Decimal
    net_taxable_annual_projected: Decimal
    net_taxable_after_impatriate: Decimal
    impatriate_enabled: bool
    impatriate_exemption_applied: bool
    impatriate_election_method: ImpatriateElectionMethod | None
    impatriate_arrival_date: datetime.date | None
    impatriate_years_remaining: int | None
    parts_used: Decimal
    pas_withheld_ytd: Decimal
    pas_withheld_projected_annual: Decimal


class InvestmentIncomeOut(BaseModel):
    """Feature I4 — realized capital gains + dividends folded into the
    estimate, only populated when `include_investments=true`."""
    realized_gains_total: Decimal
    dividends_total: Decimal
    taxable_investment_income: Decimal
    exemptions_applied: list[str]
    pfu_total_tax: Decimal
    bareme_option_total_tax: Decimal
    chosen_method: str  # "pfu" | "bareme"


class TaxEstimateOut(BaseModel):
    year: int
    bareme_tax_year_used: int
    filing_status: FilingStatus
    parts: Decimal | None
    household_gross_income_projected: Decimal
    household_taxable_income_projected: Decimal
    estimated_tax: Decimal
    quotient_familial_capped: bool
    pas_withheld_ytd_total: Decimal
    pas_withheld_projected_annual_total: Decimal
    balance: Decimal
    investment_income: InvestmentIncomeOut | None = None
    persons: list[PersonTaxEstimateOut]
    simplifications_applied: list[str]
