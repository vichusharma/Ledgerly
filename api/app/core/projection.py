"""
Goal feasibility projection — pure deterministic.

Given:
  - current portfolio value
  - expected monthly contribution
  - expected annual return
  - target amount + target date

Output:
  - projected value at target date
  - on/off track boolean
  - projected date of reaching goal (if ever within 50-year horizon)
  - required return rate to hit the goal by target date

Monte Carlo (P3):
  - sample annual returns ~ N(mu, sigma); run 1000 paths; return p10/p50/p90 bands
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from decimal import Decimal

import numpy as np
from scipy.optimize import brentq


@dataclass(frozen=True)
class FeasibilityResult:
    projected_value_at_target: Decimal
    on_track: bool
    projected_reach_date: datetime.date | None   # date projected to hit the goal
    required_annual_return: float | None         # return needed to hit exactly by target date
    months_to_target: int | None


def goal_feasibility(
    current_value: Decimal,
    monthly_contribution: Decimal,
    annual_return: Decimal,
    target_amount: Decimal,
    target_date: datetime.date,
    current_date: datetime.date | None = None,
) -> FeasibilityResult:
    """Deterministic goal feasibility projection."""
    if current_date is None:
        current_date = datetime.date.today()

    months_horizon = (
        (target_date.year - current_date.year) * 12
        + (target_date.month - current_date.month)
    )
    if months_horizon <= 0:
        on_track = current_value >= target_amount
        return FeasibilityResult(
            projected_value_at_target=current_value,
            on_track=on_track,
            projected_reach_date=current_date if on_track else None,
            required_annual_return=None,
            months_to_target=0,
        )

    monthly_r = annual_return / Decimal("12")
    value = current_value

    projected_reach_date: datetime.date | None = None
    months_to_target: int | None = None

    for month in range(1, months_horizon + 1):
        value = value * (1 + monthly_r) + monthly_contribution
        if projected_reach_date is None and value >= target_amount:
            projected_reach_date = _add_months(current_date, month)
            months_to_target = month

    projected_value = value
    on_track = projected_value >= target_amount

    # Required return: solve for r such that FV(r, months_horizon) = target_amount
    required_return: float | None = None
    target_float = float(target_amount)
    current_float = float(current_value)
    contrib_float = float(monthly_contribution)

    def fv_diff(annual_r: float) -> float:
        r = annual_r / 12
        if abs(r) < 1e-12:
            return current_float + contrib_float * months_horizon - target_float
        fv = current_float * (1 + r) ** months_horizon + \
             contrib_float * ((1 + r) ** months_horizon - 1) / r
        return fv - target_float

    try:
        required_return = brentq(fv_diff, -0.50, 5.0, xtol=1e-8, maxiter=500)
    except (ValueError, RuntimeError):
        required_return = None

    return FeasibilityResult(
        projected_value_at_target=projected_value,
        on_track=on_track,
        projected_reach_date=projected_reach_date,
        required_annual_return=required_return,
        months_to_target=months_to_target,
    )


def monte_carlo(
    current_value: float,
    monthly_contribution: float,
    annual_return_mu: float,
    annual_return_sigma: float,
    target_amount: float,
    months_horizon: int,
    n_paths: int = 1000,
    seed: int = 42,
) -> dict[str, list[float]]:
    """
    P3: Monte Carlo projection.
    Returns {"p10": [...], "p50": [...], "p90": [...]} — monthly series.
    """
    rng = np.random.default_rng(seed)
    monthly_mu = annual_return_mu / 12
    monthly_sigma = annual_return_sigma / (12 ** 0.5)

    paths = np.zeros((n_paths, months_horizon))
    values = np.full(n_paths, current_value)

    for m in range(months_horizon):
        returns = rng.normal(monthly_mu, monthly_sigma, n_paths)
        values = values * (1 + returns) + monthly_contribution
        paths[:, m] = values

    p10 = np.percentile(paths, 10, axis=0).tolist()
    p50 = np.percentile(paths, 50, axis=0).tolist()
    p90 = np.percentile(paths, 90, axis=0).tolist()

    return {"p10": p10, "p50": p50, "p90": p90}


def _add_months(d: datetime.date, months: int) -> datetime.date:
    import calendar
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    return d.replace(year=year, month=month, day=min(d.day, last_day))
