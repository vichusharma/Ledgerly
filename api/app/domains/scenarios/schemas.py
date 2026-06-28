"""Scenarios domain schemas."""
from __future__ import annotations

import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.domains.scenarios.models import ScenarioType


class ScenarioCreateIn(BaseModel):
    name: str
    type: ScenarioType = ScenarioType.invest_vs_prepay
    parameters: dict = {}
    notes: str | None = None


class ScenarioOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    name: str
    type: ScenarioType
    parameters: dict
    last_result: dict | None
    last_run_at: datetime.datetime | None
    notes: str | None
    created_at: datetime.datetime


class ReturnAssumptions(BaseModel):
    low: Decimal = Decimal("0.02")
    base: Decimal = Decimal("0.05")
    high: Decimal = Decimal("0.08")


class ScenarioRunIn(BaseModel):
    horizon_months: int = 240
    lump_sum: Decimal = Decimal("0")
    monthly: Decimal = Decimal("0")
    mortgage_id: int | None = None
    returns: ReturnAssumptions = ReturnAssumptions()


class MonthPoint(BaseModel):
    month: int
    invest: Decimal
    prepay: Decimal
    delta: Decimal


class ReturnScenario(BaseModel):
    return_label: str
    annual_return: Decimal
    invest_net_worth_end: Decimal
    prepay_net_worth_end: Decimal
    delta_end: Decimal
    breakeven_month: int | None
    interest_saved_if_prepay: Decimal
    interpretation: str
    series: list[MonthPoint]


class ScenarioResultOut(BaseModel):
    scenario_id: int
    currency: str
    results: dict[str, ReturnScenario]  # keyed by "low"|"base"|"high"


class GoalFeasibilityIn(BaseModel):
    current_value: Decimal
    monthly_contribution: Decimal
    annual_return: Decimal = Decimal("0.05")
    target_amount: Decimal
    target_date: datetime.date


class GoalFeasibilityOut(BaseModel):
    projected_value_at_target: Decimal
    on_track: bool
    projected_reach_date: datetime.date | None
    required_annual_return: float | None
    months_to_target: int | None
