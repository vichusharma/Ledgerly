"""
Portfolio performance — TWR and XIRR.

Both functions are PURE: they take cashflow lists and return numbers.
No DB, no network.

TWR (Time-Weighted Return):
    Split the period at every external cashflow (contribution/withdrawal).
    Sub-period return: r_i = (V_end - CF) / V_start - 1
    Chain-link: TWR = Π(1 + r_i) - 1

XIRR (Money-Weighted / IRR on irregular cashflows):
    Solve Σ CF_t / (1 + rate)^((t - t0)/365) = 0
    using Newton–Raphson with Brent-method fallback.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from decimal import Decimal

import numpy as np
from scipy.optimize import brentq


@dataclass(frozen=True)
class CashFlow:
    """A dated cashflow. Negative = money in (investment), positive = money out (withdrawal)."""
    date: datetime.date
    amount: float  # Use float for numeric solvers


@dataclass(frozen=True)
class SubPeriod:
    start_value: float
    end_value: float
    external_cashflow: float  # net CF during the period (+ = inflow)


def twr(sub_periods: list[SubPeriod]) -> float:
    """
    Compute Time-Weighted Return from a list of sub-periods.

    Each sub-period spans between two external cashflow events.
    The sub-period return is computed as:
        r_i = (end_value - external_cashflow) / start_value - 1

    Returns the TWR as a decimal (e.g., 0.12 = 12%).
    Returns 0.0 if no sub-periods or start values are zero.
    """
    result = 1.0
    for sp in sub_periods:
        if sp.start_value == 0.0:
            continue
        r_i = (sp.end_value - sp.external_cashflow) / sp.start_value - 1
        result *= 1 + r_i
    return result - 1.0


def xirr(cashflows: list[CashFlow]) -> float | None:
    """
    Compute XIRR (annualised IRR on irregular cashflows).

    The final cashflow must be the current portfolio value (positive, representing
    the "sale" of the portfolio).

    Returns the rate as a decimal (e.g., 0.08 = 8%) or None if no solution found.

    Uses Newton–Raphson first, then Brent fallback.
    """
    if len(cashflows) < 2:
        return None

    dates = [cf.date for cf in cashflows]
    amounts = [cf.amount for cf in cashflows]
    t0 = dates[0]
    days = [(d - t0).days for d in dates]

    def npv(rate: float) -> float:
        return sum(
            amt / (1 + rate) ** (d / 365.0)
            for amt, d in zip(amounts, days)
        )

    def npv_deriv(rate: float) -> float:
        return sum(
            -amt * (d / 365.0) / (1 + rate) ** (d / 365.0 + 1)
            for amt, d in zip(amounts, days)
            if d != 0
        )

    # Newton–Raphson
    rate = 0.1
    for _ in range(100):
        fn = npv(rate)
        dfn = npv_deriv(rate)
        if abs(dfn) < 1e-12:
            break
        rate_new = rate - fn / dfn
        if abs(rate_new - rate) < 1e-8:
            return rate_new
        rate = rate_new

    # Brent fallback
    try:
        return brentq(npv, -0.9999, 100.0, xtol=1e-8, maxiter=500)
    except (ValueError, RuntimeError):
        return None


def build_sub_periods(
    cashflows: list[CashFlow],
    start_value: float,
    end_value: float,
    period_start: datetime.date,
    period_end: datetime.date,
) -> list[SubPeriod]:
    """
    Helper: build a list of SubPeriod objects from a cashflow list.

    External cashflows split the measurement period. Between each consecutive
    pair of cashflow dates, we need a known start and end value.

    In practice, callers should provide valuation snapshots at each CF date and
    call this function to construct the sub-periods.

    This simplified version assumes the caller provides the list of (date, value)
    checkpoints and net CFs at each checkpoint.
    """
    # This is intentionally minimal; the InvestmentService builds proper sub-periods
    # from price history + lot cashflows.
    raise NotImplementedError(
        "Use InvestmentService.build_performance_sub_periods() — "
        "it hydrates values from price history."
    )
