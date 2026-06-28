"""
Golden tests for TWR and XIRR.

Reference values verified against Excel's XIRR function and the
CFA Institute's TWR examples.
"""
import datetime
from decimal import Decimal

import pytest

from app.core.performance import CashFlow, SubPeriod, twr, xirr


class TestTWR:
    def test_simple_one_period(self):
        """Single period: 10% growth, no cashflows."""
        # Start=100, end=110, no external CF
        sp = SubPeriod(start_value=100.0, end_value=110.0, external_cashflow=0.0)
        assert abs(twr([sp]) - 0.10) < 1e-6

    def test_chain_link(self):
        """Two sub-periods chain correctly."""
        sp1 = SubPeriod(start_value=100.0, end_value=110.0, external_cashflow=0.0)
        sp2 = SubPeriod(start_value=110.0, end_value=121.0, external_cashflow=0.0)
        # (1.1)(1.1) - 1 = 0.21
        assert abs(twr([sp1, sp2]) - 0.21) < 1e-6

    def test_contribution_does_not_inflate_twr(self):
        """External inflows must not inflate TWR."""
        # Period 1: value 100→150 (50% gain)
        # External inflow of 50 at boundary; new start = 200
        # Period 2: 200→240 (20% gain)
        # TWR = (1.5)(1.2) - 1 = 0.80
        sp1 = SubPeriod(start_value=100.0, end_value=150.0, external_cashflow=0.0)
        sp2 = SubPeriod(start_value=200.0, end_value=240.0, external_cashflow=50.0)
        result = twr([sp1, sp2])
        assert abs(result - 0.80) < 1e-6

    def test_zero_start_skipped(self):
        """Sub-periods with zero start value are skipped."""
        sp_zero = SubPeriod(start_value=0.0, end_value=100.0, external_cashflow=0.0)
        sp_normal = SubPeriod(start_value=100.0, end_value=110.0, external_cashflow=0.0)
        result = twr([sp_zero, sp_normal])
        assert abs(result - 0.10) < 1e-6

    def test_empty(self):
        assert twr([]) == 0.0


class TestXIRR:
    def test_simple_annual(self):
        """Invest 1000, receive 1100 exactly one year later → 10% XIRR."""
        cfs = [
            CashFlow(date=datetime.date(2023, 1, 1), amount=-1000.0),
            CashFlow(date=datetime.date(2024, 1, 1), amount=1100.0),
        ]
        result = xirr(cfs)
        assert result is not None
        assert abs(result - 0.10) < 1e-4

    def test_irregular_cashflows(self):
        """
        Excel XIRR reference:
          -1000 on 2023-01-01
          +250  on 2023-07-01  (~182 days)
          +250  on 2024-01-01  (~365 days)
          +700  on 2024-07-01  (~547 days)
        Excel XIRR ≈ 20.76%
        """
        cfs = [
            CashFlow(date=datetime.date(2023, 1, 1), amount=-1000.0),
            CashFlow(date=datetime.date(2023, 7, 1), amount=250.0),
            CashFlow(date=datetime.date(2024, 1, 1), amount=250.0),
            CashFlow(date=datetime.date(2024, 7, 1), amount=700.0),
        ]
        result = xirr(cfs)
        assert result is not None
        assert abs(result - 0.2076) < 0.002  # within 0.2pp

    def test_single_cashflow_returns_none(self):
        cfs = [CashFlow(date=datetime.date(2024, 1, 1), amount=-1000.0)]
        assert xirr(cfs) is None

    def test_negative_return(self):
        """Invest 1000, get back only 800 → negative XIRR."""
        cfs = [
            CashFlow(date=datetime.date(2023, 1, 1), amount=-1000.0),
            CashFlow(date=datetime.date(2024, 1, 1), amount=800.0),
        ]
        result = xirr(cfs)
        assert result is not None
        assert result < 0
