"""Liabilities domain models."""
from __future__ import annotations

import enum
from decimal import Decimal

import datetime

from sqlalchemy import Date, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.db import Base


class LoanType(str, enum.Enum):
    mortgage = "mortgage"
    car = "car"
    personal = "personal"
    student = "student"
    other = "other"


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[LoanType] = mapped_column(Enum(LoanType), default=LoanType.mortgage)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)

    principal: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    annual_rate: Mapped[Decimal] = mapped_column(Numeric(8, 6), nullable=False)
    term_months: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    payment_day: Mapped[int] = mapped_column(Integer, default=5)  # day of month
    currency: Mapped[str] = mapped_column(String(3), default="EUR")

    # P2: accumulated prepayments (for recompute)
    extra_principal_paid: Mapped[Decimal] = mapped_column(
        Numeric(20, 4), default=Decimal("0")
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    amortization_rows: Mapped[list["AmortizationRow"]] = relationship(
        "AmortizationRow", back_populates="loan", cascade="all, delete-orphan"
    )


class AmortizationRow(Base):
    __tablename__ = "amortization_rows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    loan_id: Mapped[int] = mapped_column(ForeignKey("loans.id"), nullable=False)
    period: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-based month number
    payment_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    payment: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    principal: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    interest: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)

    loan: Mapped["Loan"] = relationship("Loan", back_populates="amortization_rows")
