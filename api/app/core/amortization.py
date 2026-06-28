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

import datetime
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


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
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    return d.replace(year=year, month=month, day=min(d.day, last_day))


def compute_schedule(
    principal: Decimal,
    annual_rate: Decimal,
    term_months: int,
    start_date: datetime.date,
    payment_day: int = 5,
    extra_principal: Decimal = Decimal("0"),
) -> list[AmortRow]:
    """
    Compute a full French amortization schedule.

    Args:
        principal: Initial loan amount (positive).
        annual_rate: Annual interest rate as a decimal (e.g. 0.0185 for 1.85%).
        term_months: Total number of monthly payments.
        start_date: Loan start date (first payment = start_date + 1 month).
        payment_day: Day of month for payments.
        extra_principal: One-time additional principal paid upfront (prepayment).

    Returns:
        List of AmortRow, one per period.
    """
    QUANT = Decimal("0.01")

    effective_principal = principal - extra_principal
    if effective_principal <= Decimal("0"):
        return []

    monthly_rate = annual_rate / Decimal("12")

    if monthly_rate == Decimal("0"):
        emi = (effective_principal / Decimal(term_months)).quantize(QUANT, ROUND_HALF_UP)
    else:
        # EMI = P * r / (1 - (1+r)^-n)
        r = float(monthly_rate)
        n = term_months
        emi_float = float(effective_principal) * r / (1 - (1 + r) ** -n)
        emi = Decimal(str(emi_float)).quantize(QUANT, ROUND_HALF_UP)

    rows: list[AmortRow] = []
    balance = effective_principal

    for period in range(1, term_months + 1):
        # Payment date: start_date + period months, clamped to payment_day
        raw_date = _add_months(start_date, period)
        import calendar
        last_day = calendar.monthrange(raw_date.year, raw_date.month)[1]
        payment_date = raw_date.replace(day=min(payment_day, last_day))

        interest = (balance * monthly_rate).quantize(QUANT, ROUND_HALF_UP)

        if period == term_months:
            # Last period: pay off remaining balance exactly
            principal_part = balance
            payment = principal_part + interest
        else:
            principal_part = (emi - interest).quantize(QUANT, ROUND_HALF_UP)
            payment = emi

        balance = (balance - principal_part).quantize(QUANT, ROUND_HALF_UP)

        rows.append(
            AmortRow(
                period=period,
                payment_date=payment_date,
                payment=payment,
                principal=principal_part,
                interest=interest,
                balance=max(balance, Decimal("0")),
            )
        )

        if balance <= Decimal("0"):
            break

    return rows


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
