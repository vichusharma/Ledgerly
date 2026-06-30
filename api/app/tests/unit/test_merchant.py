"""Unit tests for best-effort merchant extraction from bank descriptions."""
from app.domains.transactions.merchant import normalize_merchant


def test_strips_card_prefix_date_and_city():
    assert normalize_merchant("CB CARREFOUR MARKET 12/05 PARIS") == "Carrefour Market"


def test_payment_prefix_variants_collapse_to_same_merchant():
    a = normalize_merchant("PAIEMENT CB AMAZON EU 27/06")
    b = normalize_merchant("CB AMAZON EU SARL")
    assert a == "Amazon Eu"
    assert b.startswith("Amazon Eu")


def test_direct_debit_prefix():
    assert normalize_merchant("PRLV TOTAL ENERGIE") == "Total Energie"


def test_transfer_prefix():
    assert normalize_merchant("VIR SALAIRE") == "Salaire"


def test_short_acronym_kept_uppercase():
    assert normalize_merchant("CB SNCF 14/06 LYON") == "SNCF"


def test_empty_falls_back():
    assert normalize_merchant("") == "—"


def test_strips_trailing_card_reference_number():
    assert normalize_merchant("CARTE 4978 FNAC 03/06") == "FNAC"
