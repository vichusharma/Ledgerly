"""Golden tests for invest-vs-prepay simulator."""
import datetime
from decimal import Decimal

from app.core.simulation import invest_vs_prepay


def test_basic_invest_vs_prepay():
    """High return should favour investing over prepaying."""
    results = invest_vs_prepay(
        lump_sum=Decimal("20000"),
        monthly_extra=Decimal("0"),
        horizon_months=120,
        mortgage_principal=Decimal("200000"),
        annual_mortgage_rate=Decimal("0.02"),
        mortgage_remaining_months=240,
        mortgage_start_date=datetime.date(2024, 1, 1),
        returns={"low": Decimal("0.02"), "base": Decimal("0.05"), "high": Decimal("0.08")},
        current_date=datetime.date(2024, 1, 1),
    )
    by_label = {r.return_label: r for r in results}

    # At 8% return investing beats prepaying (mortgage at 2%)
    high = by_label["high"]
    assert high.delta_end > Decimal("0"), "High return: invest should win"
    assert high.breakeven_month is not None
    assert high.breakeven_month < 120

    # At 2% return (= mortgage rate) prepaying should win or be near-zero
    low = by_label["low"]
    # Interest saved should be positive
    assert low.interest_saved_if_prepay > Decimal("0")


def test_series_length():
    results = invest_vs_prepay(
        lump_sum=Decimal("10000"),
        monthly_extra=Decimal("500"),
        horizon_months=60,
        mortgage_principal=Decimal("150000"),
        annual_mortgage_rate=Decimal("0.03"),
        mortgage_remaining_months=180,
        mortgage_start_date=datetime.date(2024, 1, 1),
        returns={"base": Decimal("0.05")},
    )
    assert len(results) == 1
    assert len(results[0].series) == 60


def test_no_lump_sum_monthly_only():
    """With no lump sum, monthly contributions still compound."""
    results = invest_vs_prepay(
        lump_sum=Decimal("0"),
        monthly_extra=Decimal("1000"),
        horizon_months=12,
        mortgage_principal=Decimal("100000"),
        annual_mortgage_rate=Decimal("0.02"),
        mortgage_remaining_months=120,
        mortgage_start_date=datetime.date(2024, 1, 1),
        returns={"base": Decimal("0.06")},
    )
    assert results[0].invest_net_worth_end > Decimal("0")
