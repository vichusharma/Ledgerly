"""
French amortization (amortissement constant / annuité constante).

The French standard is a fixed monthly payment (EMI) calculated as:

    EMI = P * r / (1 - (1+r)^-n)

where r = annual_rate/12, n = term_months.

Each row:
    interest   = remaining_balance * r
    principal  = EMI - interest
    balance    = previous_balance - principal

Pure function: no DB, no FastAPI — takes numbers, returns numbers.
"""
from __future__ import annotations

import calendar
import datetime
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

QUANT = Decimal("0.01")
DEFAULT_MAX_PERIODS = 1200  # 100 years — safety cap for manual/fixed-payment schedules


@dataclass(frozen=True)
class AmortRow:
    period: int
    payment_date: datetime.date
    payment: Decimal
    principal: Decimal
    interest: Decimal
    balance: Decimal


def _add_months(d: datetime.date, months: int) -> datetime.date:
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    # Clamp day to last day of month
    last_day = calendar.monthrange(year, month)[1]
    return d.replace(year=year, month=month, day=min(d.day, last_day))


def validate_manual_payment(balance: Decimal, annual_rate: Decimal, payment: Decimal) -> None:
    """Raise ValueError if `payment` wouldn't even cover the first period's interest
    (negative amortization — the balance would never go down)."""
    monthly_rate = annual_rate / Decimal("12")
    first_interest = (balance * monthly_rate).quantize(QUANT, ROUND_HALF_UP)
    if payment <= first_interest:
        raise ValueError(
            f"payment {payment} is too low to cover the first period's interest "
            f"({first_interest}) — the balance would never decrease"
        )


def _build_rows(
    balance: Decimal,
    monthly_rate: Decimal,
    payment: Decimal,
    start_period: int,
    anchor_date: datetime.date,
    payment_day: int,
    max_periods: int,
    fixed_period_count: int | None = None,
) -> list[AmortRow]:
    """Shared amortization loop.

    Applies `payment` each period, starting at `start_period`, with period dates computed
    as `anchor_date` + (period - start_period + 1) months. Stops when the balance reaches
    zero, or after `fixed_period_count` periods if given (used by "reduce EMI" mode, which
    holds the period count fixed rather than the payment), or raises ValueError if neither
    condition is met within `max_periods` periods (a schedule that never converges).

    The last row emitted always settles the exact remaining balance, even if that's less
    than `payment` (payoff) or — for a `fixed_period_count` schedule — whatever amount is
    left (should equal `payment` by construction if the EMI was solved correctly).
    """
    rows: list[AmortRow] = []
    period = start_period
    periods_emitted = 0

    while True:
        if fixed_period_count is not None and periods_emitted >= fixed_period_count:
            break
        if periods_emitted >= max_periods:
            raise ValueError(
                f"amortization schedule did not converge within {max_periods} periods"
            )

        raw_date = _add_months(anchor_date, period - start_period + 1)
        last_day = calendar.monthrange(raw_date.year, raw_date.month)[1]
        payment_date = raw_date.replace(day=min(payment_day, last_day))

        interest = (balance * monthly_rate).quantize(QUANT, ROUND_HALF_UP)

        is_last = (
            fixed_period_count is not None and periods_emitted == fixed_period_count - 1
        ) or (balance - (payment - interest) <= Decimal("0"))

        if is_last:
            principal_part = balance
            row_payment = principal_part + interest
        else:
            principal_part = (payment - interest).quantize(QUANT, ROUND_HALF_UP)
            row_payment = payment

        balance = (balance - principal_part).quantize(QUANT, ROUND_HALF_UP)

        rows.append(
            AmortRow(
                period=period,
                payment_date=payment_date,
                payment=row_payment,
                principal=principal_part,
                interest=interest,
                balance=max(balance, Decimal("0")),
            )
        )

        periods_emitted += 1
        period += 1

        if balance <= Decimal("0"):
            break

    return rows


def compute_schedule(
    principal: Decimal,
    annual_rate: Decimal,
    term_months: int,
    start_date: datetime.date,
    payment_day: int = 5,
    extra_principal: Decimal = Decimal("0"),
    manual_payment: Decimal | None = None,
    max_periods: int = DEFAULT_MAX_PERIODS,
) -> list[AmortRow]:
    """
    Compute a full French amortization schedule.

    Args:
        principal: Initial loan amount (positive).
        annual_rate: Annual interest rate as a decimal (e.g. 0.0185 for 1.85%).
        term_months: Total number of monthly payments (advisory only when `manual_payment`
            is set — the real row count is then whatever it takes to reach a zero balance).
        start_date: Loan start date (first payment = start_date + 1 month).
        payment_day: Day of month for payments.
        extra_principal: One-time additional principal paid upfront (prepayment).
        manual_payment: Optional fixed payment amount overriding the computed EMI (e.g. the
            bank's real quoted payment, which can differ slightly from the theoretical
            formula due to rounding or insurance riders). When set, the schedule runs until
            the balance reaches zero rather than for exactly `term_months` periods.
        max_periods: Safety cap on the number of periods generated when `manual_payment` is
            set (has no effect on the computed-EMI path, which always runs exactly
            `term_months` periods).

    Returns:
        List of AmortRow, one per period.
    """
    effective_principal = principal - extra_principal
    if effective_principal <= Decimal("0"):
        return []

    monthly_rate = annual_rate / Decimal("12")

    if manual_payment is not None:
        validate_manual_payment(effective_principal, annual_rate, manual_payment)
        return _build_rows(
            balance=effective_principal,
            monthly_rate=monthly_rate,
            payment=manual_payment,
            start_period=1,
            anchor_date=start_date,
            payment_day=payment_day,
            max_periods=max_periods,
        )

    if monthly_rate == Decimal("0"):
        emi = (effective_principal / Decimal(term_months)).quantize(QUANT, ROUND_HALF_UP)
    else:
        # EMI = P * r / (1 - (1+r)^-n)
        r = float(monthly_rate)
        n = term_months
        emi_float = float(effective_principal) * r / (1 - (1 + r) ** -n)
        emi = Decimal(str(emi_float)).quantize(QUANT, ROUND_HALF_UP)

    return _build_rows(
        balance=effective_principal,
        monthly_rate=monthly_rate,
        payment=emi,
        start_period=1,
        anchor_date=start_date,
        payment_day=payment_day,
        max_periods=term_months,
        fixed_period_count=term_months,
    )


def recompute_from_midpoint(
    outstanding_balance: Decimal,
    annual_rate: Decimal,
    payment_day: int,
    resume_period: int,
    resume_date_anchor: datetime.date,
    mode: str,
    current_payment: Decimal,
    remaining_periods_before: int,
    extra_principal: Decimal = Decimal("0"),
    max_periods: int = DEFAULT_MAX_PERIODS,
) -> list[AmortRow]:
    """
    Recompute the remaining amortization rows after a mid-loan prepayment, anchored at the
    loan's real outstanding balance as of the prepayment date (not a from-scratch day-0
    recompute) — historical rows before the prepayment are left completely untouched by
    the caller.

    Args:
        outstanding_balance: The loan's real remaining balance at the moment of prepayment
            (i.e. the balance of the last row before the application date, or the original
            principal if the prepayment happens before the first payment).
        resume_period: The period number of the first NEW row this function generates.
        resume_date_anchor: The payment_date of the period immediately before `resume_period`
            (or the loan's start_date if this is the very first period).
        mode: "reduce_term" keeps `current_payment` fixed and lets the period count shrink;
            "reduce_emi" keeps `remaining_periods_before` fixed and solves a new, lower
            payment for the reduced balance over that same count.
        current_payment: The payment amount that was in effect immediately before this
            prepayment (the anchor for "reduce_term").
        remaining_periods_before: How many periods were left (before this prepayment) —
            the anchor for "reduce_emi".
        extra_principal: The lump-sum prepayment amount, subtracted from
            `outstanding_balance` before recomputing.

    Returns:
        List of new AmortRow for the remaining life of the loan (empty if the prepayment
        fully pays off the loan).
    """
    if mode not in ("reduce_term", "reduce_emi"):
        raise ValueError(f"unknown prepayment mode: {mode!r}")

    balance_after = (outstanding_balance - extra_principal).quantize(QUANT, ROUND_HALF_UP)
    if balance_after <= Decimal("0"):
        return []

    monthly_rate = annual_rate / Decimal("12")

    if mode == "reduce_term":
        validate_manual_payment(balance_after, annual_rate, current_payment)
        return _build_rows(
            balance=balance_after,
            monthly_rate=monthly_rate,
            payment=current_payment,
            start_period=resume_period,
            anchor_date=resume_date_anchor,
            payment_day=payment_day,
            max_periods=max_periods,
        )

    # mode == "reduce_emi": keep the period count fixed, solve a new (lower) EMI.
    n = remaining_periods_before
    if n <= 0:
        raise ValueError(
            "reduce_emi requires at least one remaining period — the loan has no "
            "future payments left to spread the reduced balance over"
        )
    if monthly_rate == Decimal("0"):
        new_emi = (balance_after / Decimal(n)).quantize(QUANT, ROUND_HALF_UP)
    else:
        r = float(monthly_rate)
        new_emi_float = float(balance_after) * r / (1 - (1 + r) ** -n)
        new_emi = Decimal(str(new_emi_float)).quantize(QUANT, ROUND_HALF_UP)

    return _build_rows(
        balance=balance_after,
        monthly_rate=monthly_rate,
        payment=new_emi,
        start_period=resume_period,
        anchor_date=resume_date_anchor,
        payment_day=payment_day,
        max_periods=n,
        fixed_period_count=n,
    )


def remaining_capital(rows: list[AmortRow], as_of: datetime.date) -> Decimal:
    """Return the outstanding balance as of a given date."""
    past_rows = [r for r in rows if r.payment_date <= as_of]
    if not past_rows:
        return rows[0].balance + rows[0].principal if rows else Decimal("0")
    return past_rows[-1].balance


def interest_paid(
    rows: list[AmortRow],
    from_date: datetime.date | None = None,
    to_date: datetime.date | None = None,
) -> Decimal:
    """Sum of interest paid in an optional date range."""
    filtered = rows
    if from_date:
        filtered = [r for r in filtered if r.payment_date >= from_date]
    if to_date:
        filtered = [r for r in filtered if r.payment_date <= to_date]
    return sum((r.interest for r in filtered), Decimal("0"))
