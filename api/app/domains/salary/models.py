"""Salary domain models — French payslip ("bulletin de paie") ingestion.

Deliberately siloed from the Transactions ledger: a payslip is stored for
tax-estimation purposes only and never creates/links a Transaction, which
would double-count a bank-imported salary deposit.
"""
from __future__ import annotations

import datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db import Base


class Payslip(Base):
    __tablename__ = "payslips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id"), nullable=False)
    pay_period: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    employer: Mapped[str | None] = mapped_column(String(200), nullable=True)

    gross: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    net_taxable: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    net_before_tax: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    net_paid: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    pas_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    pas_withheld: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    # Year-to-date cumuls, as printed on the payslip's "Annuel" row.
    ytd_gross: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    ytd_net_taxable: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    ytd_pas_withheld: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("person_id", "pay_period", name="uq_payslip_person_period"),
    )
