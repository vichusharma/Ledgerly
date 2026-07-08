"""Golden tests for the tax_filing_rules engine (Feature J4, docs/Backlog.md).

Reuses the same placeholder barème as `test_tax.py` (see that file's
docstring for why) so the two engines' numbers stay directly
comparable.
"""
from __future__ import annotations

from decimal import Decimal

from app.core.tax import BaremeBracket
from app.core.tax_filing_rules import (
    CREDIT_METHOD,
    EFFECTIVE_RATE_METHOD,
    compute_effective_rate_exemption,
    compute_french_tax_attributable_to_income,
    map_estimate_to_2042_boxes,
    map_foreign_accounts_to_3916_entries,
    map_foreign_income_to_2047_lines,
    map_investment_income_to_2042_boxes,
    resolve_elimination_method,
    validate_filing_inputs,
)

BRACKETS = [
    BaremeBracket(Decimal("11497"), Decimal("0")),
    BaremeBracket(Decimal("29315"), Decimal("0.11")),
    BaremeBracket(Decimal("83823"), Decimal("0.30")),
    BaremeBracket(Decimal("180294"), Decimal("0.41")),
    BaremeBracket(None, Decimal("0.45")),
]
PLAFOND_PER_HALF_PART = Decimal("1791")


class TestComputeFrenchTaxAttributableToIncome:
    def test_zero_slice_returns_zero(self):
        result = compute_french_tax_attributable_to_income(
            Decimal("50000"), Decimal("0"), Decimal("1"), Decimal("1"),
            BRACKETS, PLAFOND_PER_HALF_PART,
        )
        assert result == Decimal("0")

    def test_slice_entirely_within_one_bracket(self):
        # 50000 total, 10000 foreign slice, single filer (parts=base_parts=1):
        # tax(50000)=8165.48, tax(40000)=5165.48 -> slice sits entirely in
        # the 30% bracket, so the marginal tax is exactly 10000*30%=3000.
        result = compute_french_tax_attributable_to_income(
            Decimal("50000"), Decimal("10000"), Decimal("1"), Decimal("1"),
            BRACKETS, PLAFOND_PER_HALF_PART,
        )
        assert result == Decimal("3000.00")

    def test_slice_larger_than_income_clamped_to_zero_base(self):
        # Slice exceeds total income -> tax(total - slice) computed on a
        # floor of 0, not a negative income.
        result = compute_french_tax_attributable_to_income(
            Decimal("5000"), Decimal("10000"), Decimal("1"), Decimal("1"),
            BRACKETS, PLAFOND_PER_HALF_PART,
        )
        assert result == Decimal("0")


class TestComputeEffectiveRateExemption:
    def test_zero_income_returns_zero_zero(self):
        rate, due = compute_effective_rate_exemption(
            Decimal("0"), Decimal("10000"), Decimal("1"), Decimal("1"),
            BRACKETS, PLAFOND_PER_HALF_PART,
        )
        assert rate == Decimal("0")
        assert due == Decimal("0")

    def test_effective_rate_and_french_tax_due(self):
        rate, due = compute_effective_rate_exemption(
            Decimal("50000"), Decimal("10000"), Decimal("1"), Decimal("1"),
            BRACKETS, PLAFOND_PER_HALF_PART,
        )
        # tax(50000)=8165.48 -> rate=8165.48/50000=0.1633096 -> 0.1633
        assert rate == Decimal("0.1633")
        # french-source income=40000, taxed at the unrounded rate:
        # 0.1633096*40000=6532.384 -> 6532.38
        assert due == Decimal("6532.38")


class TestResolveEliminationMethod:
    def test_line_override_wins(self):
        method, keys = resolve_elimination_method(EFFECTIVE_RATE_METHOD, CREDIT_METHOD)
        assert method == EFFECTIVE_RATE_METHOD
        assert keys == []

    def test_treaty_default_used_when_no_override(self):
        method, keys = resolve_elimination_method(None, EFFECTIVE_RATE_METHOD)
        assert method == EFFECTIVE_RATE_METHOD
        assert keys == []

    def test_falls_back_to_credit_method_and_flags_it(self):
        method, keys = resolve_elimination_method(None, None)
        assert method == CREDIT_METHOD
        assert keys == ["treaty_method_defaulted_unseeded_country"]


class TestMapEstimateTo2042Boxes:
    def test_single_declarant(self):
        boxes = map_estimate_to_2042_boxes([Decimal("50000")])
        assert len(boxes) == 1
        assert boxes[0].code == "1AJ"
        assert boxes[0].amount == Decimal("50000")

    def test_two_declarants(self):
        boxes = map_estimate_to_2042_boxes([Decimal("50000"), Decimal("30000")])
        assert [b.code for b in boxes] == ["1AJ", "1BJ"]

    def test_zero_salary_declarant_skipped_but_second_keeps_correct_code(self):
        boxes = map_estimate_to_2042_boxes([Decimal("0"), Decimal("30000")])
        assert len(boxes) == 1
        assert boxes[0].code == "1BJ"


class TestMapInvestmentIncomeTo2042Boxes:
    def test_zero_dividends_returns_empty(self):
        assert map_investment_income_to_2042_boxes(Decimal("0"), False) == []

    def test_pfu_chosen_uses_2ck(self):
        boxes = map_investment_income_to_2042_boxes(Decimal("1000"), True)
        assert boxes[0].code == "2CK"

    def test_bareme_chosen_uses_2dc(self):
        boxes = map_investment_income_to_2042_boxes(Decimal("1000"), False)
        assert boxes[0].code == "2DC"


class TestMapForeignIncomeTo2047Lines:
    def test_seeded_treaty_country_uses_credit_method(self):
        declarations = [{
            "source_country_code": "IN", "source_description": "Infosys",
            "gross_amount_eur": Decimal("10000"),
            "elimination_method_override": None,
        }]
        lines = map_foreign_income_to_2047_lines(
            declarations, {"IN": CREDIT_METHOD}, Decimal("50000"),
            Decimal("1"), Decimal("1"), BRACKETS, PLAFOND_PER_HALF_PART,
        )
        assert len(lines) == 1
        assert lines[0].elimination_method == CREDIT_METHOD
        assert lines[0].french_tax_credit_or_exemption == Decimal("3000.00")
        assert lines[0].simplification_keys == []

    def test_unseeded_country_falls_back_and_flags(self):
        declarations = [{
            "source_country_code": "ZZ", "source_description": "Unknown Corp",
            "gross_amount_eur": Decimal("10000"),
            "elimination_method_override": None,
        }]
        lines = map_foreign_income_to_2047_lines(
            declarations, {}, Decimal("50000"),
            Decimal("1"), Decimal("1"), BRACKETS, PLAFOND_PER_HALF_PART,
        )
        assert lines[0].elimination_method == CREDIT_METHOD
        assert lines[0].simplification_keys == ["treaty_method_defaulted_unseeded_country"]

    def test_effective_rate_method_used_when_resolved(self):
        declarations = [{
            "source_country_code": "DE", "source_description": "Deutsche AG",
            "gross_amount_eur": Decimal("10000"),
            "elimination_method_override": None,
        }]
        lines = map_foreign_income_to_2047_lines(
            declarations, {"DE": EFFECTIVE_RATE_METHOD}, Decimal("50000"),
            Decimal("1"), Decimal("1"), BRACKETS, PLAFOND_PER_HALF_PART,
        )
        assert lines[0].elimination_method == EFFECTIVE_RATE_METHOD
        assert lines[0].french_tax_credit_or_exemption == Decimal("6532.38")


class TestMapForeignAccountsTo3916Entries:
    def test_maps_fields_through(self):
        declarations = [{
            "bank_name": "State Bank of India", "country_code": "IN",
            "account_identifier_masked": "****3456",
            "opened_this_year": True, "closed_this_year": False,
        }]
        entries = map_foreign_accounts_to_3916_entries(declarations)
        assert entries[0].bank_name == "State Bank of India"
        assert entries[0].opened_this_year is True
        assert entries[0].closed_this_year is False


class TestValidateFilingInputs:
    def test_no_issues_when_everything_present(self):
        issues = validate_filing_inputs(
            has_residency=True,
            foreign_income_countries={"IN"},
            declared_foreign_account_countries={"IN"},
            declarations_missing_documents=[],
        )
        assert issues == []

    def test_missing_residency_flagged(self):
        issues = validate_filing_inputs(
            has_residency=False,
            foreign_income_countries=set(),
            declared_foreign_account_countries=set(),
            declarations_missing_documents=[],
        )
        assert "missing_residency_profile" in issues

    def test_foreign_income_without_declared_account_flagged(self):
        issues = validate_filing_inputs(
            has_residency=True,
            foreign_income_countries={"IN", "US"},
            declared_foreign_account_countries={"IN"},
            declarations_missing_documents=[],
        )
        assert issues == ["foreign_income_from_US_with_no_declared_account"]

    def test_missing_documents_flagged(self):
        issues = validate_filing_inputs(
            has_residency=True,
            foreign_income_countries=set(),
            declared_foreign_account_countries=set(),
            declarations_missing_documents=["dividend line #3"],
        )
        assert issues == ["no_source_document_for_dividend line #3"]
