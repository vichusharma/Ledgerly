"""Planning domain schemas."""
from __future__ import annotations

import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.domains.planning.models import GoalType, RecurrenceFrequency


class GoalCreateIn(BaseModel):
    name: str
    type: GoalType = GoalType.other
    target_amount: Decimal
    target_date: datetime.date | None = None
    currency: str = "EUR"
    notes: str | None = None


class GoalOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    name: str
    type: GoalType
    target_amount: Decimal
    target_date: datetime.date | None
    currency: str
    notes: str | None
    is_achieved: bool


class GoalProgressOut(BaseModel):
    goal_id: int
    current_value: Decimal
    target_amount: Decimal
    progress_pct: float
    on_track: bool
    projected_reach_date: datetime.date | None


class VacationBudgetCreateIn(BaseModel):
    name: str
    start_date: datetime.date
    end_date: datetime.date
    currency: str = "EUR"
    planned_items: list[dict] = []
    notes: str | None = None


class VacationBudgetUpdateIn(BaseModel):
    planned_items: list[dict] | None = None
    notes: str | None = None


class VacationBudgetOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    name: str
    start_date: datetime.date
    end_date: datetime.date
    currency: str
    planned_items: list
    notes: str | None
    planned_total: Decimal = Decimal("0")
    actual_total: Decimal = Decimal("0")


class RecurringExpenseCreateIn(BaseModel):
    name: str
    expected_amount: Decimal
    currency: str = "EUR"
    category_id: int | None = None
    frequency: RecurrenceFrequency = RecurrenceFrequency.monthly
    day_of_month: int | None = None


class RecurringExpenseOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    name: str
    expected_amount: Decimal
    currency: str
    category_id: int | None
    frequency: RecurrenceFrequency
    day_of_month: int | None
    is_active: bool
