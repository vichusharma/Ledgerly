"""Unit tests — pdf_payslip_parser text helpers (no real PDF needed)."""
from __future__ import annotations

import datetime
from decimal import Decimal

from app.domains.salary.parsers.pdf_payslip_parser import (
    _amount,
    _parse_employer,
    _parse_gross,
    _parse_net_before_tax,
    _parse_net_paid,
    _parse_pas_line,
    _parse_period,
)


def test_parse_amount_french_format():
    assert _amount("3.245,50") == Decimal("3245.50")


def test_parse_amount_rejects_garbage():
    assert _amount("N/A") is None


def test_parse_period_from_pay_period_line():
    text = "Etablissement : LYON\nPériode de paie du 01.06.2026 au 30.06.2026\n"
    assert _parse_period(text) == datetime.date(2026, 6, 1)


def test_parse_period_missing_returns_none():
    assert _parse_period("no period here") is None


def test_parse_employer_from_line_after_title():
    text = "Bulletin de paie\nAcme France SAS, 10, Rue de la Paix, 75002\n"
    assert _parse_employer(text) == "Acme France SAS"


def test_parse_gross_line():
    text = "1010 Salaire de Base 3.245,50\nSalaire Brut 3.245,50\n"
    assert _parse_gross(text) == Decimal("3245.50")


def test_parse_net_before_tax_line():
    text = "NET À PAYER AVANT IMPÔT SUR LE REVENU 2.987,20\n"
    assert _parse_net_before_tax(text) == Decimal("2987.20")


def test_parse_net_paid_line():
    text = "Net à Payer (en Euro): 2.650,10\n"
    assert _parse_net_paid(text) == Decimal("2650.10")


def test_parse_pas_line_extracts_rate_and_withheld():
    line = (
        "/5T0 Impôt sur le revenu prélevé à la source Taux personnalisé "
        "3.100,00 8,50% 263,50"
    )
    rate, withheld = _parse_pas_line(line)
    assert rate == Decimal("8.50")
    assert withheld == Decimal("263.50")


def test_parse_pas_line_missing_returns_none_pair():
    rate, withheld = _parse_pas_line("nothing relevant here")
    assert rate is None
    assert withheld is None
