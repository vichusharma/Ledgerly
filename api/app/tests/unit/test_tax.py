"""
Golden tests for the French income-tax engine (Feature I3).

Reference values hand-computed against a 2025-Loi-de-Finances-shaped
barème (0%/11%/30%/41%/45%, thresholds 11497/29315/83823/180294) and a
1,791 EUR quotient-familial plafonnement per half-part — see
docs/Backlog.md's "Documented simplifications" for why this placeholder
barème is used pending an official 2026 publication.
"""
import datetime
from decimal import Decimal

from app.core.tax import (
    BaremeBracket,
    LotEvent,
    WrapperGain,
    apply_bareme,
    apply_impatriate_exemption,
    apply_wrapper_exemptions,
    compare_pfu_vs_bareme,
    compute_parts,
    compute_pfu,
    compute_quotient_tax,
    compute_realized_gains_for_year,
    impatriate_years_remaining,
    is_minor_dependent,
    project_annual_from_ytd,
    reconcile_withholding,
    sum_dividends_for_year,
)

BRACKETS = [
    BaremeBracket(Decimal("11497"), Decimal("0")),
    BaremeBracket(Decimal("29315"), Decimal("0.11")),
    BaremeBracket(Decimal("83823"), Decimal("0.30")),
    BaremeBracket(Decimal("180294"), Decimal("0.41")),
    BaremeBracket(None, Decimal("0.45")),
]
PLAFOND_PER_HALF_PART = Decimal("1791")


class TestApplyBareme:
    def test_zero_income(self):
        assert apply_bareme(Decimal("0"), BRACKETS) == Decimal("0")

    def test_negative_income_returns_zero(self):
        assert apply_bareme(Decimal("-500"), BRACKETS) == Decimal("0")

    def test_within_zero_bracket(self):
        assert apply_bareme(Decimal("11497"), BRACKETS) == Decimal("0")

    def test_within_second_bracket(self):
        # (20000 - 11497) * 0.11 = 935.33
        assert apply_bareme(Decimal("20000"), BRACKETS) == Decimal("935.33")

    def test_spans_three_brackets_golden(self):
        # 0% up to 11497; 11% on (29315-11497)=17818 -> 1959.98;
        # 30% on (40000-29315)=10685 -> 3205.50; total 5165.48
        assert apply_bareme(Decimal("40000"), BRACKETS) == Decimal("5165.48")

    def test_top_bracket_no_upper_bound(self):
        # 45% bracket applies above 180294 with no cap.
        tax = apply_bareme(Decimal("200000"), BRACKETS)
        # sanity: tax on 200000 must exceed tax on 180294
        assert tax > apply_bareme(Decimal("180294"), BRACKETS)


class TestComputeParts:
    def test_single_no_dependents(self):
        assert compute_parts("single", 0) == Decimal("1")

    def test_single_one_dependent(self):
        assert compute_parts("single", 1) == Decimal("1.5")

    def test_married_no_dependents(self):
        assert compute_parts("married_pacs", 0) == Decimal("2")

    def test_married_two_dependents(self):
        assert compute_parts("married_pacs", 2) == Decimal("3")

    def test_married_three_dependents_third_child_is_full_part(self):
        assert compute_parts("married_pacs", 3) == Decimal("4")

    def test_adult_dependent_is_a_flat_full_part(self):
        # 1 adult dependent, no minors: 2 + 1 = 3, not the 0.5 a minor would get.
        assert compute_parts("married_pacs", 0, 1) == Decimal("3")

    def test_adult_dependents_dont_share_the_minor_progression(self):
        # 2 adults: flat 1 each = 2, regardless of the minor first-two-at-0.5 rule.
        assert compute_parts("single", 0, 2) == Decimal("3")

    def test_minor_and_adult_dependents_combine(self):
        # 1 minor (+0.5) + 1 adult (+1) on top of married base (2) = 3.5.
        assert compute_parts("married_pacs", 1, 1) == Decimal("3.5")

    def test_negative_adult_count_clamped_to_zero(self):
        assert compute_parts("single", 0, -1) == Decimal("1")


class TestIsMinorDependent:
    def test_no_birth_date_defaults_to_minor(self):
        assert is_minor_dependent(None, datetime.date(2026, 12, 31)) is True

    def test_seventeen_year_old_is_minor(self):
        assert is_minor_dependent(datetime.date(2009, 6, 1), datetime.date(2026, 12, 31)) is True

    def test_eighteen_year_old_is_adult(self):
        assert is_minor_dependent(datetime.date(2008, 6, 1), datetime.date(2026, 12, 31)) is False

    def test_day_before_eighteenth_birthday_still_minor(self):
        # Turns 18 on Dec 31 2026 — one day earlier they're still 17.
        assert is_minor_dependent(datetime.date(2008, 12, 31), datetime.date(2026, 12, 30)) is True

    def test_turns_eighteen_exactly_on_reference_date_is_adult(self):
        assert is_minor_dependent(datetime.date(2008, 12, 31), datetime.date(2026, 12, 31)) is False


class TestComputeQuotientTax:
    def test_parts_equal_base_parts_no_plafonnement_check(self):
        tax, capped = compute_quotient_tax(
            Decimal("40000"), Decimal("1"), Decimal("1"), BRACKETS, PLAFOND_PER_HALF_PART
        )
        assert tax == Decimal("5165.48")
        assert capped is False

    def test_reduction_under_cap_not_capped(self):
        # income=50000, married_pacs + 1 dependent -> parts=2.5, base_parts=2.
        # Both 50000/2.5=20000 and 50000/2=25000 fall inside the 11% bracket only.
        tax, capped = compute_quotient_tax(
            Decimal("50000"), Decimal("2.5"), Decimal("2"), BRACKETS, PLAFOND_PER_HALF_PART
        )
        # tax_at_parts = 935.33 * 2.5 = 2338.325 -> rounds to 2338.33 (half-up)
        assert tax == Decimal("2338.33")
        assert capped is False

    def test_reduction_over_cap_is_capped(self):
        # income=99000, married_pacs + 2 dependents -> parts=3, base_parts=2.
        # tax_at_parts (33000/part) = 3065.48 * 3 = 9196.44
        # tax_at_base (49500/part) = 8015.48 * 2 = 16030.96
        # extra_half_parts=2, max_reduction=2*1791=3582
        # actual_reduction=16030.96-9196.44=6834.52 > 3582 -> capped
        # capped_tax = 16030.96 - 3582 = 12448.96
        tax, capped = compute_quotient_tax(
            Decimal("99000"), Decimal("3"), Decimal("2"), BRACKETS, PLAFOND_PER_HALF_PART
        )
        assert tax == Decimal("12448.96")
        assert capped is True


class TestApplyImpatriateExemption:
    def test_disabled_returns_unchanged(self):
        income, applied = apply_impatriate_exemption(Decimal("50000"), False, "flat_30")
        assert income == Decimal("50000")
        assert applied is False

    def test_flat_30_exempts_30_percent(self):
        income, applied = apply_impatriate_exemption(Decimal("50000"), True, "flat_30")
        assert income == Decimal("35000")
        assert applied is True

    def test_specific_premium_not_computed(self):
        income, applied = apply_impatriate_exemption(Decimal("50000"), True, "specific_premium")
        assert income == Decimal("50000")
        assert applied is False

    def test_none_method_returns_unchanged(self):
        income, applied = apply_impatriate_exemption(Decimal("50000"), True, None)
        assert income == Decimal("50000")
        assert applied is False


class TestImpatriateYearsRemaining:
    def test_mid_window(self):
        remaining = impatriate_years_remaining(
            datetime.date(2023, 9, 1), datetime.date(2026, 7, 6)
        )
        assert remaining == 4

    def test_arrival_year_itself(self):
        remaining = impatriate_years_remaining(
            datetime.date(2026, 1, 1), datetime.date(2026, 7, 6)
        )
        assert remaining == 7

    def test_expired_window_clamped_to_zero(self):
        remaining = impatriate_years_remaining(
            datetime.date(2015, 1, 1), datetime.date(2026, 1, 1)
        )
        assert remaining == 0


class TestProjectAnnualFromYtd:
    def test_halfway_through_year(self):
        assert project_annual_from_ytd(Decimal("30000"), 6) == Decimal("60000")

    def test_full_year(self):
        assert project_annual_from_ytd(Decimal("60000"), 12) == Decimal("60000")

    def test_zero_month_returns_zero(self):
        assert project_annual_from_ytd(Decimal("10000"), 0) == Decimal("0")


class TestReconcileWithholding:
    def test_owes_balance_positive(self):
        assert reconcile_withholding(Decimal("12000"), Decimal("10000")) == Decimal("2000")

    def test_refund_balance_negative(self):
        assert reconcile_withholding(Decimal("8000"), Decimal("10000")) == Decimal("-2000")


def _ev(lot_type: str, qty: str, price: str, fees: str, y: int, m: int, d: int) -> LotEvent:
    return LotEvent(lot_type, Decimal(qty), Decimal(price), Decimal(fees), datetime.date(y, m, d))


class TestComputeRealizedGainsForYear:
    def test_simple_buy_then_sell_same_year(self):
        events = [
            _ev("buy", "10", "100", "0", 2026, 1, 5),
            _ev("sell", "10", "150", "0", 2026, 6, 1),
        ]
        # proceeds 1500 - cost 1000 = 500
        assert compute_realized_gains_for_year(events, 2026) == Decimal("500")

    def test_average_cost_across_two_buys(self):
        events = [
            _ev("buy", "10", "100", "0", 2025, 1, 1),
            _ev("buy", "10", "200", "0", 2025, 6, 1),
            _ev("sell", "5", "300", "0", 2026, 3, 1),
        ]
        # avg cost = 3000/20 = 150/unit; cost of 5 sold = 750; proceeds 1500; gain 750
        assert compute_realized_gains_for_year(events, 2026) == Decimal("750")

    def test_sell_in_other_year_excluded(self):
        events = [
            _ev("buy", "10", "100", "0", 2024, 1, 1),
            _ev("sell", "10", "150", "0", 2025, 6, 1),
        ]
        assert compute_realized_gains_for_year(events, 2026) == Decimal("0")

    def test_fees_reduce_gain(self):
        events = [
            _ev("buy", "10", "100", "10", 2026, 1, 1),
            _ev("sell", "10", "150", "5", 2026, 6, 1),
        ]
        # cost basis (10*100)+10=1010, avg cost 101/unit; proceeds (10*150)-5=1495
        # cost of 10 sold = 1010; gain = 485
        assert compute_realized_gains_for_year(events, 2026) == Decimal("485")

    def test_sell_with_no_prior_buys_is_pure_proceeds(self):
        events = [_ev("sell", "5", "100", "0", 2026, 1, 1)]
        assert compute_realized_gains_for_year(events, 2026) == Decimal("500")

    def test_loss_is_negative(self):
        events = [
            _ev("buy", "10", "200", "0", 2026, 1, 1),
            _ev("sell", "10", "150", "0", 2026, 6, 1),
        ]
        assert compute_realized_gains_for_year(events, 2026) == Decimal("-500")


class TestSumDividendsForYear:
    def test_sums_dividends_in_year(self):
        events = [
            _ev("dividend", "1", "50", "0", 2026, 3, 1),
            _ev("dividend", "1", "30", "0", 2026, 9, 1),
        ]
        assert sum_dividends_for_year(events, 2026) == Decimal("80")

    def test_excludes_other_years_and_non_dividend_lots(self):
        events = [
            _ev("dividend", "1", "50", "0", 2025, 3, 1),
            _ev("buy", "10", "100", "0", 2026, 1, 1),
        ]
        assert sum_dividends_for_year(events, 2026) == Decimal("0")


class TestApplyWrapperExemptions:
    def test_pea_past_five_years_fully_exempt(self):
        gains = [WrapperGain("PEA", datetime.date(2018, 1, 1), Decimal("1000"))]
        taxable, keys = apply_wrapper_exemptions(gains, "single", datetime.date(2026, 1, 1))
        assert taxable == Decimal("0")
        assert keys == ["pea_five_year_exemption"]

    def test_pea_before_five_years_fully_taxable(self):
        gains = [WrapperGain("PEA", datetime.date(2024, 1, 1), Decimal("1000"))]
        taxable, keys = apply_wrapper_exemptions(gains, "single", datetime.date(2026, 1, 1))
        assert taxable == Decimal("1000")
        assert keys == []

    def test_av_past_eight_years_abattement_single(self):
        gains = [WrapperGain("AV", datetime.date(2015, 1, 1), Decimal("6000"))]
        taxable, keys = apply_wrapper_exemptions(gains, "single", datetime.date(2026, 1, 1))
        # 6000 - 4600 abattement = 1400
        assert taxable == Decimal("1400")
        assert keys == ["av_eight_year_abattement"]

    def test_av_past_eight_years_abattement_married(self):
        gains = [WrapperGain("AV", datetime.date(2015, 1, 1), Decimal("10000"))]
        taxable, keys = apply_wrapper_exemptions(gains, "married_pacs", datetime.date(2026, 1, 1))
        # 10000 - 9200 abattement = 800
        assert taxable == Decimal("800")
        assert keys == ["av_eight_year_abattement"]

    def test_av_abattement_pooled_across_accounts(self):
        gains = [
            WrapperGain("AV", datetime.date(2015, 1, 1), Decimal("3000")),
            WrapperGain("AV", datetime.date(2016, 1, 1), Decimal("3000")),
        ]
        taxable, keys = apply_wrapper_exemptions(gains, "single", datetime.date(2026, 1, 1))
        # pooled 6000 - 4600 abattement = 1400, not 4600 applied twice
        assert taxable == Decimal("1400")
        assert keys == ["av_eight_year_abattement"]

    def test_av_before_eight_years_fully_taxable(self):
        gains = [WrapperGain("AV", datetime.date(2022, 1, 1), Decimal("1000"))]
        taxable, keys = apply_wrapper_exemptions(gains, "single", datetime.date(2026, 1, 1))
        assert taxable == Decimal("1000")
        assert keys == []

    def test_cto_never_exempt(self):
        gains = [WrapperGain("CTO", datetime.date(2010, 1, 1), Decimal("1000"))]
        taxable, keys = apply_wrapper_exemptions(gains, "single", datetime.date(2026, 1, 1))
        assert taxable == Decimal("1000")
        assert keys == []

    def test_unknown_wrapper_facts_fully_taxable(self):
        gains = [WrapperGain(None, None, Decimal("1000"))]
        taxable, keys = apply_wrapper_exemptions(gains, "single", datetime.date(2026, 1, 1))
        assert taxable == Decimal("1000")
        assert keys == []

    def test_loss_never_exempted_flows_through(self):
        gains = [WrapperGain("PEA", datetime.date(2018, 1, 1), Decimal("-500"))]
        taxable, keys = apply_wrapper_exemptions(gains, "single", datetime.date(2026, 1, 1))
        assert taxable == Decimal("-500")
        assert keys == []


class TestComputePfu:
    def test_flat_128_pct(self):
        assert compute_pfu(Decimal("1000")) == Decimal("128.00")

    def test_zero_or_negative_returns_zero(self):
        assert compute_pfu(Decimal("0")) == Decimal("0")
        assert compute_pfu(Decimal("-100")) == Decimal("0")


class TestComparePfuVsBareme:
    def test_zero_investment_income_is_a_noop(self):
        salary_tax = apply_bareme(Decimal("40000"), BRACKETS)
        one = Decimal("1")
        chosen, pfu_tax, bareme_tax = compare_pfu_vs_bareme(
            Decimal("40000"), Decimal("0"), one, one, BRACKETS, PLAFOND_PER_HALF_PART
        )
        assert chosen == "pfu"
        assert pfu_tax == bareme_tax == salary_tax

    def test_pfu_cheaper_at_high_marginal_rate(self):
        # 40000 taxable already deep in higher brackets; adding 3000 more
        # investment income to the barème costs more than the flat 12.8%.
        one = Decimal("1")
        chosen, pfu_tax, bareme_tax = compare_pfu_vs_bareme(
            Decimal("100000"), Decimal("3000"), one, one, BRACKETS, PLAFOND_PER_HALF_PART
        )
        assert chosen == "pfu"
        assert pfu_tax < bareme_tax

    def test_bareme_cheaper_when_combined_income_stays_in_zero_bracket(self):
        # Both salary (5000) and investment income (3000) stay under the
        # 11497 zero-rate threshold even combined, so barème (0) beats PFU's
        # flat 12.8% on the investment slice (384).
        one = Decimal("1")
        chosen, pfu_tax, bareme_tax = compare_pfu_vs_bareme(
            Decimal("5000"), Decimal("3000"), one, one, BRACKETS, PLAFOND_PER_HALF_PART
        )
        assert chosen == "bareme"
        assert bareme_tax == Decimal("0")
        assert pfu_tax == Decimal("384.00")
