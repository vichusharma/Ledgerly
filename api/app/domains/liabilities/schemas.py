"""Liabilities domain schemas."""
from __future__ import annotations

import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.domains.liabilities.models import LoanType


class LoanCreateIn(BaseModel):
    name: str
    type: LoanType = LoanType.mortgage
    account_id: int
    principal: Decimal
    annual_rate: Decimal
    term_months: int
    start_date: datetime.date
    payment_day: int = 5
    currency: str = "EUR"
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
    notes: str | None


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
    reduction_mode: str = "term"  # "term" | "payment"
    applied_date: datetime.date | None = None
