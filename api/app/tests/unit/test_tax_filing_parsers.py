"""Unit tests — Epic J document parsers (Feature J2, docs/Backlog.md).

Follows `test_pdf_payslip_parser.py`'s precedent of testing helper
functions directly with raw text, plus (since no real sample document
exists for any of these four types) one synthetic-PDF round trip per
parser via `reportlab` to confirm the pdfplumber wiring itself works,
not just the regexes.
"""
from __future__ import annotations

import datetime
from decimal import Decimal

from app.domains.tax_filing.parsers._common import (
    find_labeled_value,
    parse_amount,
    parse_date,
    parse_int,
    parse_percent,
    parse_shares,
)
from app.domains.tax_filing.parsers.espp_purchase_parser import parse_pdf_espp_purchase
from app.domains.tax_filing.parsers.foreign_bank_statement_parser import (
    parse_pdf_foreign_bank_statement,
)
from app.domains.tax_filing.parsers.foreign_dividend_statement_parser import (
    parse_pdf_foreign_dividend_statement,
)
from app.domains.tax_filing.parsers.rsu_vesting_parser import parse_pdf_rsu_vesting
from app.tests.unit._pdf_test_helpers import make_text_pdf

# -- _common.py helpers -------------------------------------------------

def test_find_labeled_value_matches_label_on_line():
    text = "Grant Date: 01/15/2023\nOther line"
    assert find_labeled_value(text, ("Grant Date",)) == "01/15/2023"


def test_find_labeled_value_missing_returns_none():
    assert find_labeled_value("no labels here", ("Grant Date",)) is None


def test_parse_date_iso_format():
    assert parse_date("2026-01-15") == datetime.date(2026, 1, 15)


def test_parse_date_us_slash_format():
    assert parse_date("01/15/2026") == datetime.date(2026, 1, 15)


def test_parse_date_garbage_returns_none():
    assert parse_date("not a date") is None


def test_parse_amount_extracts_decimal():
    assert parse_amount("$1,234.56") == Decimal("1234.56")


def test_parse_amount_missing_returns_none():
    assert parse_amount("no amount") is None


def test_parse_percent_extracts_decimal():
    assert parse_percent("Discount: 15%") == Decimal("15")


def test_parse_shares_extracts_decimal():
    assert parse_shares("123.5 shares") == Decimal("123.5")


def test_parse_int_extracts_int():
    assert parse_int("Cliff: 12 months") == 12


# -- RSU vesting parser ---------------------------------------------------

def test_parse_pdf_rsu_vesting_extracts_known_fields():
    pdf = make_text_pdf([
        "RSU Vest Confirmation",
        "Grant Date: 01/15/2023",
        "Vest Date: 01/15/2026",
        "Total Shares Granted: 400 shares",
        "Shares Vested: 100 shares",
        "Grant Price: $45.00",
        "Fair Market Value: $62.50",
        "Cliff: 12 months",
        "Vesting Period: 48 months",
    ])
    preview = parse_pdf_rsu_vesting(pdf)
    assert preview.grant_date == datetime.date(2023, 1, 15)
    assert preview.vest_date == datetime.date(2026, 1, 15)
    assert preview.total_shares == Decimal("400")
    assert preview.vested_shares == Decimal("100")
    assert preview.grant_price == Decimal("45.00")
    assert preview.vest_fmv == Decimal("62.50")
    assert preview.cliff_months == 12
    assert preview.vesting_months == 48


def test_parse_pdf_rsu_vesting_missing_fields_are_none():
    pdf = make_text_pdf(["Unrelated document with no known labels"])
    preview = parse_pdf_rsu_vesting(pdf)
    assert preview.grant_date is None
    assert preview.total_shares is None


# -- ESPP purchase parser --------------------------------------------------

def test_parse_pdf_espp_purchase_extracts_known_fields():
    pdf = make_text_pdf([
        "ESPP Purchase Confirmation",
        "Purchase Date: 06/30/2026",
        "Shares Purchased: 25.75 shares",
        "Purchase Price: $38.25",
        "Fair Market Value: $45.00",
        "Discount: 15%",
    ])
    preview = parse_pdf_espp_purchase(pdf)
    assert preview.purchase_date == datetime.date(2026, 6, 30)
    assert preview.shares == Decimal("25.75")
    assert preview.purchase_price == Decimal("38.25")
    assert preview.fmv_at_purchase == Decimal("45.00")
    assert preview.discount_pct == Decimal("15")


# -- Foreign dividend statement parser -------------------------------------

def test_parse_pdf_foreign_dividend_statement_extracts_known_fields():
    pdf = make_text_pdf([
        "Dividend Statement",
        "Payer: Acme Corp Inc",
        "Payment Date: 03/31/2026",
        "Gross Dividend: $500.00",
        "Tax Withheld: $75.00",
    ])
    preview = parse_pdf_foreign_dividend_statement(pdf)
    assert preview.source_description == "Acme Corp Inc"
    assert preview.income_date == datetime.date(2026, 3, 31)
    assert preview.gross_amount_eur == Decimal("500.00")
    assert preview.foreign_tax_paid_eur == Decimal("75.00")
    # Country is never guessed — always left for the user to pick.
    assert preview.source_country_code is None


# -- Foreign bank statement parser -----------------------------------------

def test_parse_pdf_foreign_bank_statement_masks_account_number():
    pdf = make_text_pdf([
        "Bank Statement",
        "Bank Name: State Bank of India",
        "Account Number: 1234567890123456",
    ])
    preview = parse_pdf_foreign_bank_statement(pdf)
    assert preview.bank_name == "State Bank of India"
    assert preview.account_identifier_masked == "****3456"
    assert preview.country_code is None
