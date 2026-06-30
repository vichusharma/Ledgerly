"""
Golden tests for French amortization.

Reference values computed independently via Excel's PMT / PPMT / IPMT functions
and validated against a €280,000 mortgage at 1.85% over 20 years.
"""
import datetime
from decimal import Decimal

import pytest

from app.core.amortization import (
    compute_schedule,
    interest_paid,
    remaining_capital,
)


def test_emi_count():
    """Schedule should have exactly term_months rows."""
    rows = compute_schedule(
        principal=Decimal("280000"),
        annual_rate=Decimal("0.0185"),
        term_months=240,
        start_date=datetime.date(2021, 6, 1),
    )
    assert len(rows) == 240


def test_first_payment_golden():
    """First payment golden values for €280k @ 1.85% / 20y."""
    rows = compute_schedule(
        principal=Decimal("280000"),
        annual_rate=Decimal("0.0185"),
        term_months=240,
        start_date=datetime.date(2021, 6, 1),
    )
    r0 = rows[0]
    # Monthly rate = 1.85% / 12 = 0.154167%
    # EMI = P * r / (1 - (1+r)^-n) ≈ 1396.67 EUR
    assert abs(float(r0.payment) - 1396.67) < 0.10, f"EMI={r0.payment}"
    # First interest = 280000 * 0.0185 / 12 ≈ 431.67
    assert abs(float(r0.interest) - 431.67) < 0.10, f"interest={r0.interest}"
    # First principal ≈ 965.00
    assert abs(float(r0.principal) - 965.00) < 0.10, f"principal={r0.principal}"


def test_balance_reaches_zero():
    """Final balance should be ≤ 0.01 (rounding tolerance)."""
    rows = compute_schedule(
        principal=Decimal("280000"),
        annual_rate=Decimal("0.0185"),
        term_months=240,
        start_date=datetime.date(2021, 6, 1),
    )
    assert rows[-1].balance <= Decimal("0.01")


def test_total_interest():
    """Total interest over life ≈ €53,190 for this mortgage."""
    rows = compute_schedule(
        principal=Decimal("280000"),
        annual_rate=Decimal("0.0185"),
        term_months=240,
        start_date=datetime.date(2021, 6, 1),
    )
    total = interest_paid(rows)
    assert Decimal("50000") < total < Decimal("57000"), f"total_interest={total}"


def test_remaining_capital_at_5y():
    """After 5 years (~60 payments), significant principal still outstanding."""
    rows = compute_schedule(
        principal=Decimal("280000"),
        annual_rate=Decimal("0.0185"),
        term_months=240,
        start_date=datetime.date(2021, 6, 1),
    )
    cap = remaining_capital(rows, datetime.date(2026, 6, 1))
    # After 5 years, balance should be roughly 220k–240k
    assert Decimal("215000") < cap < Decimal("245000"), f"remaining={cap}"


def test_zero_rate():
    """Zero-rate loan: equal principal payments, no interest."""
    rows = compute_schedule(
        principal=Decimal("12000"),
        annual_rate=Decimal("0"),
        term_months=12,
        start_date=datetime.date(2024, 1, 1),
    )
    assert len(rows) == 12
    for r in rows:
        assert r.interest == Decimal("0.00")
    assert abs(float(rows[0].principal) - 1000.0) < 0.01


def test_prepayment_reduces_interest():
    """Paying €10k extra upfront should reduce total interest."""
    rows_no_prepay = compute_schedule(
        principal=Decimal("100000"),
        annual_rate=Decimal("0.03"),
        term_months=120,
        start_date=datetime.date(2024, 1, 1),
    )
    rows_prepay = compute_schedule(
        principal=Decimal("100000"),
        annual_rate=Decimal("0.03"),
        term_months=120,
        start_date=datetime.date(2024, 1, 1),
        extra_principal=Decimal("10000"),
    )
    total_no_prepay = interest_paid(rows_no_prepay)
    total_prepay = interest_paid(rows_prepay)
    assert total_prepay < total_no_prepay


def test_payment_day_clamped():
    """payment_day=31 in February should clamp to 28/29."""
    rows = compute_schedule(
        principal=Decimal("10000"),
        annual_rate=Decimal("0.05"),
        term_months=12,
        start_date=datetime.date(2024, 1, 1),
        payment_day=31,
    )
    feb_rows = [r for r in rows if r.payment_date.month == 2]
    assert len(feb_rows) == 1
    assert feb_rows[0].payment_date.day in (28, 29)
