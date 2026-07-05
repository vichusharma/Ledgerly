"""Unit tests — pdf_valuation_parser text helpers (no real PDF needed)."""
from __future__ import annotations

from decimal import Decimal

from app.domains.imports.parsers.pdf_valuation_parser import (
    _AMT_RE,
    _AS_OF_RE,
    _parse_amount,
)


def test_parse_amount_french_format():
    assert _parse_amount("12 345,67") == Decimal("12345.67")


def test_parse_amount_anglo_format():
    assert _parse_amount("8000.00") == Decimal("8000.00")


def test_parse_amount_rejects_garbage():
    assert _parse_amount("N/A") is None


def test_trailing_amount_regex_with_euro_suffix():
    m = _AMT_RE.search("Fonds Euro Suravenir 12 345,67 €")
    assert m is not None
    assert _parse_amount(m.group(1)) == Decimal("12345.67")


def test_as_of_regex_variants():
    for line in (
        "Situation au 31/12/2025",
        "Arrêté au 31-12-2025",
        "valeur au 31.12.2025",
    ):
        assert _AS_OF_RE.search(line), line
