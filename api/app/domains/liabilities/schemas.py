"""Liabilities domain schemas."""
from __future__ import annotations

import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.domains.liabilities.models import LoanType


class LoanCreateIn(BaseModel):
    name: str
    type: LoanType = LoanType.mortgage
    principal: Decimal
    annual_rate: Decimal
    term_months: int
    start_date: datetime.date
    payment_day: int = 5
    currency: str = "EUR"
    manual_payment: Decimal | None = None
    notes: str | None = None

    # The linked liability Account is auto-created from these fields — the caller
    # never supplies an account_id directly.
    institution: str | None = None
    owner_id: int
    joint_owner_id: int | None = None
    ownership_pct: Decimal = Decimal("100.00")


class LoanUpdateIn(BaseModel):
    """Cosmetic/administrative edits only. Changing principal/rate/term/
    manual_payment/start_date has no well-defined "preserve history" rule (unlike
    a prepayment, there's no natural recompute anchor), so it's deliberately out
    of scope here — use the prepayment flow for anything that changes the schedule."""
    name: str | None = None
    type: LoanType | None = None
    payment_day: int | None = None
    institution: str | None = None
    notes: str | None = None


class LoanOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    name: str
    type: LoanType
    account_id: int
    principal: Decimal
    annual_rate: Decimal
    term_months: int
    start_date: datetime.date
    payment_day: int
    currency: str
    extra_principal_paid: Decimal
    manual_payment: Decimal | None
    notes: str | None
    # Lives on the linked Account, not Loan — attached by the service layer after
    # validation (there's no `institution` column on `Loan` itself).
    institution: str | None = None


class AmortRowOut(BaseModel):
    model_config = {"from_attributes": True}
    period: int
    payment_date: datetime.date
    payment: Decimal
    principal: Decimal
    interest: Decimal
    balance: Decimal


class DebtSummaryOut(BaseModel):
    loan_id: int
    remaining_capital: Decimal
    interest_paid_ytd: Decimal
    interest_paid_total: Decimal
    total_payments_remaining: int
    next_payment_date: datetime.date | None
    next_payment_amount: Decimal | None


class PrepaymentIn(BaseModel):
    amount: Decimal
    reduction_mode: str = "term"  # "term" (reduce duration) | "payment" (reduce EMI)
    applied_date: datetime.date | None = None


class PrepaymentScenarioOut(BaseModel):
    mode: str  # "reduce_term" | "reduce_emi"
    new_payment: Decimal
    payoff_date: datetime.date | None
    remaining_periods: int
    total_interest_remaining: Decimal
    interest_saved_vs_baseline: Decimal


class PrepaymentPreviewOut(BaseModel):
    loan_id: int
    as_of: datetime.date
    amount: Decimal
    outstanding_balance_before: Decimal
    reduce_term: PrepaymentScenarioOut
    reduce_emi: PrepaymentScenarioOut
