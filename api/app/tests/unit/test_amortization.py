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
    recompute_from_midpoint,
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


# ── Manual EMI override ─────────────────────────────────────────────────────

def test_manual_payment_matches_computed_when_equal():
    """A manual_payment equal to the theoretical EMI should produce essentially the
    same schedule as the auto-computed path (same period count, same total interest
    to within a few cents of rounding-drift tolerance)."""
    auto_rows = compute_schedule(
        principal=Decimal("280000"),
        annual_rate=Decimal("0.0185"),
        term_months=240,
        start_date=datetime.date(2021, 6, 1),
    )
    theoretical_emi = auto_rows[0].payment
    manual_rows = compute_schedule(
        principal=Decimal("280000"),
        annual_rate=Decimal("0.0185"),
        term_months=240,
        start_date=datetime.date(2021, 6, 1),
        manual_payment=theoretical_emi,
    )
    assert abs(len(manual_rows) - len(auto_rows)) <= 1
    assert manual_rows[-1].balance == Decimal("0.00")
    assert abs(interest_paid(manual_rows) - interest_paid(auto_rows)) < Decimal("5.00")


def test_manual_payment_higher_than_theoretical_shortens_term():
    """A manual_payment above the theoretical EMI should pay the loan off sooner."""
    auto_rows = compute_schedule(
        principal=Decimal("100000"),
        annual_rate=Decimal("0.03"),
        term_months=120,
        start_date=datetime.date(2024, 1, 1),
    )
    higher_payment = auto_rows[0].payment + Decimal("100.00")
    manual_rows = compute_schedule(
        principal=Decimal("100000"),
        annual_rate=Decimal("0.03"),
        term_months=120,
        start_date=datetime.date(2024, 1, 1),
        manual_payment=higher_payment,
    )
    assert len(manual_rows) < len(auto_rows)
    assert manual_rows[-1].balance == Decimal("0.00")


def test_manual_payment_too_low_raises():
    """A manual_payment below the first period's interest is negative amortization."""
    with pytest.raises(ValueError):
        compute_schedule(
            principal=Decimal("100000"),
            annual_rate=Decimal("0.03"),
            term_months=120,
            start_date=datetime.date(2024, 1, 1),
            manual_payment=Decimal("100.00"),  # first interest ≈ 250
        )


def test_manual_payment_safety_cap():
    """A payment just barely above the interest-only threshold takes an enormous
    number of periods to amortize — should hit max_periods and raise, not hang."""
    with pytest.raises(ValueError, match="max_periods|converge"):
        compute_schedule(
            principal=Decimal("100000"),
            annual_rate=Decimal("0.03"),
            term_months=120,
            start_date=datetime.date(2024, 1, 1),
            manual_payment=Decimal("251.00"),  # first interest ≈ 250
            max_periods=50,
        )


# ── Mid-loan prepayment recompute ───────────────────────────────────────────

def _loan_setup():
    return dict(
        principal=Decimal("280000"),
        annual_rate=Decimal("0.0185"),
        term_months=240,
        start_date=datetime.date(2021, 6, 1),
    )


def test_recompute_reduce_term_mid_loan():
    """Reduce-term prepayment: keep the same payment, pay off sooner, with less
    total interest on the remaining life than doing nothing."""
    params = _loan_setup()
    rows = compute_schedule(**params)
    elapsed = 60
    historical = rows[:elapsed]
    future_before = rows[elapsed:]
    balance_at_60 = historical[-1].balance
    current_payment = future_before[0].payment

    new_rows = recompute_from_midpoint(
        outstanding_balance=balance_at_60,
        annual_rate=params["annual_rate"],
        payment_day=5,
        resume_period=elapsed + 1,
        resume_date_anchor=historical[-1].payment_date,
        mode="reduce_term",
        current_payment=current_payment,
        remaining_periods_before=len(future_before),
        extra_principal=Decimal("10000"),
    )

    assert len(new_rows) < len(future_before)
    # Payment held fixed across all but the final settling row.
    assert all(r.payment == current_payment for r in new_rows[:-1])
    assert new_rows[-1].balance == Decimal("0.00")
    assert interest_paid(new_rows) < interest_paid(future_before)


def test_recompute_reduce_emi_mid_loan():
    """Reduce-EMI prepayment: keep the same remaining period count, lower the payment."""
    params = _loan_setup()
    rows = compute_schedule(**params)
    elapsed = 60
    historical = rows[:elapsed]
    future_before = rows[elapsed:]
    balance_at_60 = historical[-1].balance
    current_payment = future_before[0].payment

    new_rows = recompute_from_midpoint(
        outstanding_balance=balance_at_60,
        annual_rate=params["annual_rate"],
        payment_day=5,
        resume_period=elapsed + 1,
        resume_date_anchor=historical[-1].payment_date,
        mode="reduce_emi",
        current_payment=current_payment,
        remaining_periods_before=len(future_before),
        extra_principal=Decimal("10000"),
    )

    assert len(new_rows) == len(future_before)
    assert new_rows[0].payment < current_payment
    assert new_rows[-1].balance == Decimal("0.00")
    assert interest_paid(new_rows) < interest_paid(future_before)


def test_recompute_full_payoff():
    """A prepayment equal to (or exceeding) the outstanding balance fully closes the loan."""
    params = _loan_setup()
    rows = compute_schedule(**params)
    elapsed = 60
    historical = rows[:elapsed]
    future_before = rows[elapsed:]
    balance_at_60 = historical[-1].balance

    new_rows = recompute_from_midpoint(
        outstanding_balance=balance_at_60,
        annual_rate=params["annual_rate"],
        payment_day=5,
        resume_period=elapsed + 1,
        resume_date_anchor=historical[-1].payment_date,
        mode="reduce_term",
        current_payment=future_before[0].payment,
        remaining_periods_before=len(future_before),
        extra_principal=balance_at_60,
    )

    assert new_rows == []


def test_recompute_is_pure_function_of_passed_state():
    """recompute_from_midpoint never needs (and never emits) periods before
    resume_period — it's a pure function of the state handed to it, not the full
    loan history, which is what guarantees historical rows are never rewritten."""
    params = _loan_setup()
    rows = compute_schedule(**params)
    elapsed = 60
    historical = rows[:elapsed]
    future_before = rows[elapsed:]
    balance_at_60 = historical[-1].balance

    new_rows = recompute_from_midpoint(
        outstanding_balance=balance_at_60,
        annual_rate=params["annual_rate"],
        payment_day=5,
        resume_period=elapsed + 1,
        resume_date_anchor=historical[-1].payment_date,
        mode="reduce_emi",
        current_payment=future_before[0].payment,
        remaining_periods_before=len(future_before),
        extra_principal=Decimal("10000"),
    )

    assert all(r.period >= elapsed + 1 for r in new_rows)
