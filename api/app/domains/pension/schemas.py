"""Pension domain schemas — French state pension projection."""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class PensionProjectionIn(BaseModel):
    birth_year: int
    career_start_year: int
    current_annual_salary: Decimal
    salary_growth_rate: Decimal
    planned_retirement_year: int
    bonus_quarters: int = 0


class SensitivityRow(BaseModel):
    retirement_age: float
    retirement_year: int
    quarters_validated: int
    rate_applied: Decimal
    decote_quarters: int
    surcote_quarters: int
    monthly_base: Decimal
    monthly_complementary: Decimal
    monthly_total: Decimal
    replacement_ratio: Decimal
    achieves_full_rate: bool


class PensionProjectionOut(BaseModel):
    sam: Decimal
    quarters_validated: int
    quarters_required: int
    total_agirc_arrco_points: Decimal
    planned: SensitivityRow
    sensitivity: list[SensitivityRow]
