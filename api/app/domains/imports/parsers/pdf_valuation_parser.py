"""PDF valuation-statement parser (assurance-vie / wrapper annual statements).

Unlike pdf_parser.py (which extracts transaction rows), this extracts
*candidate fund valuations*: (label, amount) pairs. It makes no attempt to
decide which rows are real holdings vs. totals/fees — every plausible row is
returned and the user filters/edits them in the review screen before anything
is saved. Layouts vary widely between insurers, so silent guessing is unsafe.
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from io import BytesIO

import pdfplumber

from app.domains.imports.parsers import csv_parser

# Trailing amount, French or Anglo format — same pattern family as pdf_parser.
_AMT_RE = re.compile(
    r"(-?\(?\s*\d[\d\s  ]*(?:[,\.]\d{1,2})?\)?)\s*(?:EUR|€)?\s*$"
)
# "situation au 31/12/2025", "arrêté au 31-12-2025", "au 31.12.2025"
_AS_OF_RE = re.compile(
    r"(?:situation\s+au|arr[êe]t[ée]\s+au|valeur\s+au|\bau)\s+"
    r"(\d{2}[/\-\.]\d{2}[/\-\.]\d{4})",
    re.IGNORECASE,
)
# Lines that are clearly not fund rows even if they end with an amount.
_NOISE_RE = re.compile(
    r"^\s*(page|t[ée]l|fax|siren|siret|tva|iban|bic)\b", re.IGNORECASE
)


class ValuationCandidate:
    __slots__ = ("label", "value")

    def __init__(self, label: str, value: Decimal) -> None:
        self.label = label
        self.value = value


class ValuationPreview:
    __slots__ = ("as_of_date", "candidates")

    def __init__(self, as_of_date: str | None, candidates: list[ValuationCandidate]) -> None:
        self.as_of_date = as_of_date
        self.candidates = candidates


def _parse_amount(raw: str) -> Decimal | None:
    """Trailing-amount string → Decimal, inferring the decimal separator.

    The separator is whichever of ``,``/``.`` is followed by exactly 1-2 final
    digits ("12 345,67" → ",", "8000.00" → "."). Guessing by trial order would
    silently misread anglo amounts (comma-mode turns "8000.00" into 800000).
    """
    s = raw.strip()
    if re.search(r",\d{1,2}\)?\s*$", s):
        sep = ","
    elif re.search(r"\.\d{1,2}\)?\s*$", s):
        sep = "."
    else:
        sep = ","
    try:
        amount = csv_parser.parse_amount(s, sep)
    except (InvalidOperation, ValueError):
        return None
    return amount if amount != Decimal("0") else None


def parse_pdf_valuation(content: bytes) -> ValuationPreview:
    """Extract candidate (fund label, value) rows + best-effort as-of date."""
    as_of: str | None = None
    candidates: list[ValuationCandidate] = []
    seen: set[tuple[str, str]] = set()

    with pdfplumber.open(BytesIO(content)) as pdf:
        for page in pdf.pages:
            # 1. Table rows: label = first non-empty cell, value = last amount cell.
            for table in page.extract_tables():
                for row in table or []:
                    cells = [str(c or "").strip() for c in row]
                    cells = [c for c in cells if c]
                    if len(cells) < 2:
                        continue
                    label = cells[0]
                    value = None
                    for cell in reversed(cells[1:]):
                        value = _parse_amount(cell)
                        if value is not None:
                            break
                    if value is None or len(label) < 3 or not re.search(r"[A-Za-zÀ-ÿ]{3}", label):
                        continue
                    _add(candidates, seen, label, value)

            # 2. Text lines: as-of date + fallback label/amount rows.
            text = page.extract_text() or ""
            for line in text.splitlines():
                if as_of is None:
                    m = _AS_OF_RE.search(line)
                    if m:
                        try:
                            as_of = csv_parser.parse_date(m.group(1), "%d/%m/%Y").isoformat()
                        except ValueError:
                            pass
                if _NOISE_RE.search(line):
                    continue
                m_amt = _AMT_RE.search(line)
                if not m_amt:
                    continue
                label = line[: m_amt.start()].strip(" |-·.…")
                if len(label) < 3 or not re.search(r"[A-Za-zÀ-ÿ]{3}", label):
                    continue
                value = _parse_amount(m_amt.group(1))
                if value is None:
                    continue
                _add(candidates, seen, label, value)

    return ValuationPreview(as_of_date=as_of, candidates=candidates)


def _add(
    candidates: list[ValuationCandidate],
    seen: set[tuple[str, str]],
    label: str,
    value: Decimal,
) -> None:
    label = re.sub(r"\s+", " ", label).strip()
    key = (label.lower(), str(value))
    if key in seen:
        return
    seen.add(key)
    candidates.append(ValuationCandidate(label=label, value=value))
