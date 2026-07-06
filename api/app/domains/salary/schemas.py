"""Salary domain schemas."""
from __future__ import annotations

import datetime
from decimal import Decimal

from pydantic import BaseModel


class PayslipPreviewOut(BaseModel):
    """Best-effort candidate extracted from a payslip PDF — no DB write.

    Every field is nullable: the user reviews and fills in/corrects
    anything the parser missed before confirming.
    """
    pay_period: datetime.date | None = None
    employer: str | None = None
    gross: Decimal | None = None
    net_taxable: Decimal | None = None
    net_before_tax: Decimal | None = None
    net_paid: Decimal | None = None
    pas_rate: Decimal | None = None
    pas_withheld: Decimal | None = None
    ytd_gross: Decimal | None = None
    ytd_net_taxable: Decimal | None = None
    ytd_pas_withheld: Decimal | None = None


class PayslipConfirmIn(BaseModel):
    """Reviewed/corrected payslip fields, ready to save."""
    person_id: int
    pay_period: datetime.date
    employer: str | None = None
    gross: Decimal | None = None
    net_taxable: Decimal | None = None
    net_before_tax: Decimal | None = None
    net_paid: Decimal | None = None
    pas_rate: Decimal | None = None
    pas_withheld: Decimal | None = None
    ytd_gross: Decimal | None = None
    ytd_net_taxable: Decimal | None = None
    ytd_pas_withheld: Decimal | None = None
    notes: str | None = None


class PayslipOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    person_id: int
    pay_period: datetime.date
    employer: str | None
    gross: Decimal | None
    net_taxable: Decimal | None
    net_before_tax: Decimal | None
    net_paid: Decimal | None
    pas_rate: Decimal | None
    pas_withheld: Decimal | None
    ytd_gross: Decimal | None
    ytd_net_taxable: Decimal | None
    ytd_pas_withheld: Decimal | None
    notes: str | None
