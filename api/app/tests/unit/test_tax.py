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
    apply_bareme,
    apply_impatriate_exemption,
    compute_parts,
    compute_quotient_tax,
    impatriate_years_remaining,
    project_annual_from_ytd,
    reconcile_withholding,
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
