"""
Invest-vs-prepay simulator — pure deterministic projection.

Two parallel monthly projections over N months:

  PREPAY PATH:
    Extra €X reduces mortgage principal → regenerate amortization → interest saved.
    Remaining mortgage savings invested at return r each month.

  INVEST PATH:
    Extra €X invested at compound return r; mortgage runs to original schedule.

Output per scenario (low/base/high):
  - Monthly net-worth delta series (invest_path[m] - prepay_path[m])
  - Breakeven month (first month invest path overtakes prepay, or None)
  - Final net-worth for each path

All amounts in EUR. Pure: takes scalars, returns dicts.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from decimal import Decimal
from typing import NamedTuple

from app.core.amortization import compute_schedule


class MonthPoint(NamedTuple):
    month: int
    invest: Decimal
    prepay: Decimal
    delta: Decimal


@dataclass(frozen=True)
class ScenarioResult:
    return_label: str           # "low" | "base" | "high"
    annual_return: Decimal
    invest_net_worth_end: Decimal
    prepay_net_worth_end: Decimal
    delta_end: Decimal
    breakeven_month: int | None
    interest_saved_if_prepay: Decimal
    series: list[MonthPoint]
    interpretation: str


def invest_vs_prepay(
    lump_sum: Decimal,
    monthly_extra: Decimal,
    horizon_months: int,
    mortgage_principal: Decimal,
    annual_mortgage_rate: Decimal,
    mortgage_remaining_months: int,
    mortgage_start_date: datetime.date,
    returns: dict[str, Decimal],          # {"low": 0.02, "base": 0.05, "high": 0.08}
    current_date: datetime.date | None = None,
) -> list[ScenarioResult]:
    """
    Run the invest-vs-prepay simulation for each return scenario.

    The 'current_date' marks the start of the projection (default: today).
    """
    if current_date is None:
        current_date = datetime.date.today()

    results: list[ScenarioResult] = []

    # Original amortization (no prepay) — for interest cost baseline
    original_schedule = compute_schedule(
        principal=mortgage_principal,
        annual_rate=annual_mortgage_rate,
        term_months=mortgage_remaining_months,
        start_date=current_date,
    )
    original_total_interest = sum(r.interest for r in original_schedule)

    for label, annual_return in returns.items():
        monthly_r = annual_return / Decimal("12")

        # ── PREPAY PATH ────────────────────────────────────────────────────
        # Apply lump sum as extra principal upfront; monthly_extra paid monthly
        prepay_schedule = compute_schedule(
            principal=mortgage_principal,
            annual_rate=annual_mortgage_rate,
            term_months=mortgage_remaining_months,
            start_date=current_date,
            extra_principal=lump_sum,
        )
        prepay_total_interest = sum(r.interest for r in prepay_schedule)
        interest_saved = original_total_interest - prepay_total_interest

        # Track prepay-path net worth: savings from interest + invested monthly_extra
        prepay_series: list[Decimal] = []
        prepay_invested = Decimal("0")   # grows from reinvesting mortgage savings
        for month in range(1, horizon_months + 1):
            # In prepay path, the monthly_extra also reduces debt (we treat it
            # as if invested in the mortgage at the mortgage rate)
            prepay_invested = prepay_invested * (1 + monthly_r) + monthly_extra
            # Cumulative interest saved up to this month
            months_so_far = min(month, len(prepay_schedule))
            cum_interest_saved = sum(r.interest for r in original_schedule[:months_so_far]) - \
                                  sum(r.interest for r in prepay_schedule[:months_so_far])
            prepay_nw = lump_sum + prepay_invested + cum_interest_saved
            prepay_series.append(prepay_nw)

        # ── INVEST PATH ────────────────────────────────────────────────────
        invest_series: list[Decimal] = []
        portfolio = lump_sum   # Invested immediately
        monthly_portfolio = Decimal("0")
        for month in range(1, horizon_months + 1):
            portfolio = portfolio * (1 + monthly_r)
            monthly_portfolio = monthly_portfolio * (1 + monthly_r) + monthly_extra
            invest_nw = portfolio + monthly_portfolio
            invest_series.append(invest_nw)

        # ── SERIES & BREAKEVEN ─────────────────────────────────────────────
        series: list[MonthPoint] = []
        breakeven_month: int | None = None
        for month in range(1, horizon_months + 1):
            invest_nw = invest_series[month - 1]
            prepay_nw = prepay_series[month - 1]
            delta = invest_nw - prepay_nw
            series.append(MonthPoint(month=month, invest=invest_nw, prepay=prepay_nw, delta=delta))
            if breakeven_month is None and delta > Decimal("0"):
                breakeven_month = month

        invest_end = invest_series[-1]
        prepay_end = prepay_series[-1]
        delta_end = invest_end - prepay_end

        if delta_end > Decimal("0"):
            interpretation = (
                f"At {label} ({annual_return*100:.1f}%) investing beats prepaying "
                f"after month {breakeven_month}."
            )
        else:
            interpretation = (
                f"At {label} ({annual_return*100:.1f}%) prepaying wins "
                f"(saves {interest_saved:.2f} EUR in interest)."
            )

        results.append(ScenarioResult(
            return_label=label,
            annual_return=annual_return,
            invest_net_worth_end=invest_end,
            prepay_net_worth_end=prepay_end,
            delta_end=delta_end,
            breakeven_month=breakeven_month,
            interest_saved_if_prepay=interest_saved,
            series=series,
            interpretation=interpretation,
        ))

    return results
