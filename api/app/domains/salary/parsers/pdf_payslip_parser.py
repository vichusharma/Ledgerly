"""French payslip ("bulletin de paie") PDF parser.

Same philosophy as ``pdf_valuation_parser.py``: extract every plausible
known field, never guess silently when a field can't be found. Every
result field is nullable and reviewed/corrected by the user before
anything is saved — payslip layouts vary between employers/payroll
providers (verified against a large French employer's 2025-renovated
"bulletin de paie" template; tune the regexes below if another
employer's layout doesn't match).

Two extraction strategies are combined:
1. The "Mensuel"/"Annuel" summary table (Brut Imposable / Net Imposable /
   Prélèvement à la source columns) — positional table cells survive
   blank columns far more reliably than text-line regexes, and this is
   also the only place the year-to-date cumuls appear.
2. Text-line regexes for fields that aren't in that table (gross salary
   line, net-before-tax, net-paid, PAS rate, pay period, employer).
"""
from __future__ import annotations

import datetime
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from io import BytesIO

import pdfplumber

from app.domains.imports.parsers import csv_parser

_PERIOD_RE = re.compile(r"[Pp][ée]riode de paie du\s+(\d{2})[.\-/](\d{2})[.\-/](\d{4})")
_GROSS_RE = re.compile(r"Salaire\s+Brut\s+([\d.\s]+,\d{2})", re.IGNORECASE)
_NET_BEFORE_TAX_RE = re.compile(
    r"NET\s*[ÀA]\s*PAYER\s+AVANT\s+IMP[ÔO]T\s+SUR\s+LE\s+REVENU\s+([\d.\s]+,\d{2})",
    re.IGNORECASE,
)
_NET_PAID_RE = re.compile(
    r"Net\s*[àa]\s*Payer\s*\(en\s*Euro\)\s*:?\s*([\d.\s]+,\d{2})", re.IGNORECASE
)
_PAS_LINE_RE = re.compile(r"pr[ée]lev[ée]e?\s+[àa]\s+la\s+source", re.IGNORECASE)
_PERCENT_RE = re.compile(r"(\d+[,.]\d+)\s*%")
_AMOUNT_TOKEN_RE = re.compile(r"\d[\d ]*,\d{2}")
_BULLETIN_TITLE_RE = re.compile(r"^bulletin de paie$", re.IGNORECASE)


class PayslipPreview:
    __slots__ = (
        "pay_period", "employer", "gross", "net_taxable", "net_before_tax",
        "net_paid", "pas_rate", "pas_withheld",
        "ytd_gross", "ytd_net_taxable", "ytd_pas_withheld",
    )

    def __init__(self, **kwargs: object) -> None:
        for slot in self.__slots__:
            setattr(self, slot, kwargs.get(slot))


def _norm(s: str) -> str:
    """Lowercase + strip accents, so header/label matching survives typos
    like the real template's "Prélevement" (missing accent on the è)."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().replace("\n", " ").strip()


def _amount(raw: str) -> Decimal | None:
    try:
        val = csv_parser.parse_amount(raw, ",")
    except (InvalidOperation, ValueError):
        return None
    return val if val != Decimal("0") else None


def _parse_period(text: str) -> datetime.date | None:
    m = _PERIOD_RE.search(text)
    if not m:
        return None
    day, month, year = (int(g) for g in m.groups())
    try:
        return datetime.date(year, month, 1)
    except ValueError:
        return None


def _parse_employer(text: str) -> str | None:
    """First non-empty line after the "Bulletin de paie" title is the
    employer's name + address, comma-separated — take the part before
    the first comma."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for i, line in enumerate(lines):
        if _BULLETIN_TITLE_RE.match(line):
            if i + 1 < len(lines):
                return lines[i + 1].split(",")[0].strip() or None
            break
    return None


def _parse_gross(text: str) -> Decimal | None:
    m = _GROSS_RE.search(text)
    return _amount(m.group(1)) if m else None


def _parse_net_before_tax(text: str) -> Decimal | None:
    m = _NET_BEFORE_TAX_RE.search(text)
    return _amount(m.group(1)) if m else None


def _parse_net_paid(text: str) -> Decimal | None:
    m = _NET_PAID_RE.search(text)
    return _amount(m.group(1)) if m else None


def _parse_pas_line(text: str) -> tuple[Decimal | None, Decimal | None]:
    """Return (rate_pct, withheld_amount) from the PAS line, e.g.
    "Impôt sur le revenu prélevé à la source Taux personnalisé
    3.100,00 10,80% 692,60" → base 4200.00 (net imposable, already
    captured via the summary table), rate 10.80%, withheld 692.60.
    """
    for line in text.splitlines():
        if not _PAS_LINE_RE.search(line):
            continue
        pct_m = _PERCENT_RE.search(line)
        rate = _amount(pct_m.group(1)) if pct_m else None
        remainder = (line[: pct_m.start()] + " " + line[pct_m.end():]) if pct_m else line
        tokens = _AMOUNT_TOKEN_RE.findall(remainder)
        amounts = [a for tok in tokens if (a := _amount(tok)) is not None]
        withheld = amounts[-1] if amounts else None
        return rate, withheld
    return None, None


def _find_col(header_cells: list[str], needle: str) -> int | None:
    for i, cell in enumerate(header_cells):
        if needle in cell:
            return i
    return None


def _row_amount(row: list, idx: int | None) -> Decimal | None:
    if idx is None or idx >= len(row):
        return None
    raw = row[idx]
    if raw is None:
        return None
    return _amount(str(raw).strip())


def _parse_cumuls_table(pdf: pdfplumber.PDF) -> dict[str, Decimal | None]:
    """Extract the "Mensuel"/"Annuel" summary row (Brut Imposable / Net
    Imposable / Prélèvement à la source columns). Some payslip layouts
    repeat this table's header on every page but only fill in values on
    one — the first non-empty value found (scanning in page order) wins.
    """
    result: dict[str, Decimal | None] = {
        "gross": None, "net_taxable": None, "pas_withheld": None,
        "ytd_gross": None, "ytd_net_taxable": None, "ytd_pas_withheld": None,
    }
    for page in pdf.pages:
        for table in page.extract_tables():
            if not table:
                continue
            header_cells = [_norm(str(c or "")) for c in table[0]]
            gross_idx = _find_col(header_cells, "brut imposable")
            net_idx = _find_col(header_cells, "net imposable")
            pas_idx = _find_col(header_cells, "prelevement")
            if gross_idx is None and net_idx is None and pas_idx is None:
                continue
            for row in table[1:]:
                if not row:
                    continue
                label = _norm(str(row[0] or ""))
                if label == "mensuel":
                    keys = ("gross", "net_taxable", "pas_withheld")
                elif label == "annuel":
                    keys = ("ytd_gross", "ytd_net_taxable", "ytd_pas_withheld")
                else:
                    continue
                for key, idx in zip(keys, (gross_idx, net_idx, pas_idx)):
                    if result[key] is None:
                        result[key] = _row_amount(row, idx)
    return result


def parse_pdf_payslip(content: bytes) -> PayslipPreview:
    """Extract a best-effort candidate for every known payslip field."""
    with pdfplumber.open(BytesIO(content)) as pdf:
        full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        cumuls = _parse_cumuls_table(pdf)

    pas_rate, pas_withheld_from_line = _parse_pas_line(full_text)

    return PayslipPreview(
        pay_period=_parse_period(full_text),
        employer=_parse_employer(full_text),
        gross=cumuls["gross"] or _parse_gross(full_text),
        net_taxable=cumuls["net_taxable"],
        net_before_tax=_parse_net_before_tax(full_text),
        net_paid=_parse_net_paid(full_text),
        pas_rate=pas_rate,
        pas_withheld=cumuls["pas_withheld"] or pas_withheld_from_line,
        ytd_gross=cumuls["ytd_gross"],
        ytd_net_taxable=cumuls["ytd_net_taxable"],
        ytd_pas_withheld=cumuls["ytd_pas_withheld"],
    )
