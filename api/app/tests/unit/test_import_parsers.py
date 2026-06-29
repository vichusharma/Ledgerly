"""Unit tests for the statement parser layer (CSV/OFX/QIF/CAMT)."""
import datetime
from decimal import Decimal

from app.domains.imports.parsers import csv_parser, parse_non_csv, presets
from app.domains.imports.parsers.detect import detect_format


# ── CSV ─────────────────────────────────────────────────────────────────────

def test_csv_detect_columns_does_not_pick_date_valeur_as_amount():
    """Regression: 'Date valeur' must never resolve as the amount column."""
    headers = ["Date", "Date valeur", "Libellé", "Débit euros", "Crédit euros"]
    cols = csv_parser.detect_columns(headers)
    assert cols["date"] == "Date"
    assert cols["amount"] is None            # no signed amount column exists
    assert cols["debit"] == "Débit euros"
    assert cols["credit"] == "Crédit euros"
    assert cols["description"] == "Libellé"


def test_csv_split_debit_credit_french_format():
    text = (
        "Relevé de compte\n"
        "Titulaire;REDACTED\n"
        "Date;Date valeur;Libellé;Débit euros;Crédit euros\n"
        "16/05/2026;16/05/2026;Courses;8 994,00;\n"
        "17/05/2026;17/05/2026;Salaire;;1 200,50\n"
    )
    headers, rows, delimiter = csv_parser.read_rows(text)
    assert delimiter == ";"
    cols = csv_parser.detect_columns(headers)
    txns = csv_parser.build_txns(rows, cols, "%d/%m/%Y", ",")
    assert len(txns) == 2
    assert txns[0].date == datetime.date(2026, 5, 16)
    assert txns[0].amount == Decimal("-8994.00")     # debit → negative
    assert txns[0].description == "Courses"
    assert txns[1].amount == Decimal("1200.50")      # credit → positive


def test_csv_signed_amount():
    text = "Date;Libellé;Montant\n01/02/2026;Test;-12,34\n"
    headers, rows, _ = csv_parser.read_rows(text)
    cols = csv_parser.detect_columns(headers)
    txns = csv_parser.build_txns(rows, cols, "%d/%m/%Y", ",")
    assert txns[0].amount == Decimal("-12.34")


def test_preset_match_by_institution_substring():
    assert presets.match("Crédit Agricole Île-de-France") is not None
    assert presets.match("Boursorama Banque")["delimiter"] == ";"
    assert presets.match("Some Unknown Bank") is None
    assert presets.match(None) is None


# ── OFX ─────────────────────────────────────────────────────────────────────

_OFX = b"""OFXHEADER:100
DATA:OFXSGML
VERSION:102

<OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS><CURDEF>EUR</CURDEF>
<BANKACCTFROM><BANKID>123</BANKID><ACCTID>456</ACCTID><ACCTTYPE>CHECKING</ACCTTYPE></BANKACCTFROM>
<BANKTRANLIST>
<STMTTRN><TRNTYPE>DEBIT</TRNTYPE><DTPOSTED>20260516</DTPOSTED><TRNAMT>-42.50</TRNAMT><FITID>T1</FITID><NAME>Courses</NAME></STMTTRN>
<STMTTRN><TRNTYPE>CREDIT</TRNTYPE><DTPOSTED>20260517</DTPOSTED><TRNAMT>1200.00</TRNAMT><FITID>T2</FITID><NAME>Salaire</NAME></STMTTRN>
</BANKTRANLIST></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>
"""


def test_ofx_parse():
    assert detect_format("statement.ofx", _OFX) == "ofx"
    txns = parse_non_csv("ofx", _OFX)
    assert len(txns) == 2
    assert txns[0].amount == Decimal("-42.50")
    assert txns[0].date == datetime.date(2026, 5, 16)
    assert txns[1].amount == Decimal("1200.00")


# ── QIF ─────────────────────────────────────────────────────────────────────

_QIF = b"""!Type:Bank
D16/05/2026
T-42,50
PCourses
^
D17/05/2026
T1200.00
PSalaire
^
"""


def test_qif_parse():
    assert detect_format("export.qif", _QIF) == "qif"
    txns = parse_non_csv("qif", _QIF)
    assert len(txns) == 2
    assert txns[0].date == datetime.date(2026, 5, 16)
    assert txns[0].amount == Decimal("-42.50")
    assert txns[0].description == "Courses"
    assert txns[1].amount == Decimal("1200.00")


# ── CAMT.053 ─────────────────────────────────────────────────────────────────

_CAMT = b"""<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.02">
  <BkToCstmrStmt><Stmt>
    <Ntry>
      <Amt Ccy="EUR">42.50</Amt>
      <CdtDbtInd>DBIT</CdtDbtInd>
      <BookgDt><Dt>2026-05-16</Dt></BookgDt>
      <NtryDtls><TxDtls><RmtInf><Ustrd>Courses</Ustrd></RmtInf></TxDtls></NtryDtls>
    </Ntry>
    <Ntry>
      <Amt Ccy="EUR">1200.00</Amt>
      <CdtDbtInd>CRDT</CdtDbtInd>
      <BookgDt><Dt>2026-05-17</Dt></BookgDt>
      <NtryDtls><TxDtls><RmtInf><Ustrd>Salaire</Ustrd></RmtInf></TxDtls></NtryDtls>
    </Ntry>
  </Stmt></BkToCstmrStmt>
</Document>
"""


def test_camt_parse():
    assert detect_format("statement.xml", _CAMT) == "camt"
    txns = parse_non_csv("camt", _CAMT)
    assert len(txns) == 2
    assert txns[0].amount == Decimal("-42.50")        # DBIT → negative
    assert txns[0].date == datetime.date(2026, 5, 16)
    assert txns[0].description == "Courses"
    assert txns[1].amount == Decimal("1200.00")        # CRDT → positive
