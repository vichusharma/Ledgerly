"""Planning domain models — goals, vacation budgets, recurring expenses."""
from __future__ import annotations

import enum
from decimal import Decimal
import datetime

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.db import Base


class GoalType(str, enum.Enum):
    fi_number = "fi_number"
    house_payoff = "house_payoff"
    target_portfolio = "target_portfolio"
    other = "other"


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[GoalType] = mapped_column(Enum(GoalType), default=GoalType.other)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    target_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_achieved: Mapped[bool] = mapped_column(Boolean, default=False)


class VacationBudget(Base):
    __tablename__ = "vacation_budgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    # Planned line items: [{"label": "Flights", "amount": 1200.00}, ...]
    planned_items: Mapped[list] = mapped_column(JSONB, default=list)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class RecurrenceFrequency(str, enum.Enum):
    monthly = "monthly"
    quarterly = "quarterly"
    annual = "annual"


class RecurringExpense(Base):
    """Expected recurring expense — used to flag missing transactions (P2)."""
    __tablename__ = "recurring_expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    expected_amount: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    frequency: Mapped[RecurrenceFrequency] = mapped_column(
        Enum(RecurrenceFrequency), default=RecurrenceFrequency.monthly
    )
    day_of_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
