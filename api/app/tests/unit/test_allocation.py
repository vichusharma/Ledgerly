"""Tests for allocation computation."""
from decimal import Decimal

from app.core.allocation import compute_allocation


def test_allocation_sums_to_100():
    holdings = {"equity": Decimal("70000"), "bond": Decimal("20000"), "cash": Decimal("10000")}
    targets = {"equity": Decimal("70"), "bond": Decimal("20"), "cash": Decimal("10")}
    slices = compute_allocation(holdings, targets)
    total_pct = sum(s.actual_pct for s in slices)
    assert abs(float(total_pct) - 100.0) < 0.1


def test_drift_sign():
    holdings = {"equity": Decimal("80000"), "bond": Decimal("20000")}
    targets = {"equity": Decimal("70"), "bond": Decimal("30")}
    slices = {s.asset_class: s for s in compute_allocation(holdings, targets)}
    # equity overweight → positive drift
    assert slices["equity"].drift_pct > 0
    # bond underweight → negative drift
    assert slices["bond"].drift_pct < 0


def test_zero_holdings():
    """Zero portfolio → all actual_pct = 0."""
    holdings: dict = {}
    targets = {"equity": Decimal("60"), "bond": Decimal("40")}
    slices = compute_allocation(holdings, targets)
    for s in slices:
        assert s.actual_pct == Decimal("0")
        assert s.market_value == Decimal("0")


def test_unknown_class_in_holdings():
    """A class in holdings but not in targets → target_pct = 0, drift = actual_pct."""
    holdings = {"equity": Decimal("50000"), "crypto": Decimal("10000")}
    targets = {"equity": Decimal("100")}
    slices = {s.asset_class: s for s in compute_allocation(holdings, targets)}
    assert slices["crypto"].target_pct == Decimal("0")
    assert slices["crypto"].drift_pct == slices["crypto"].actual_pct
