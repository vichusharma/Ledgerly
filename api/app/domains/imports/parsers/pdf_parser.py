"""PDF bank-statement parser using pdfplumber.

Strategy:
1. Structured table extraction — pdfplumber finds embedded table grids and returns
   a list-of-rows per page.  Works for most modern bank PDFs (BNP, CA, SG…).
2. Text-line fallback — if no table with recognisable headers is found, we scan
   each text line for a leading date + trailing amount and extract everything in
   between as the description.
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from io import BytesIO

import pdfplumber

from app.domains.imports.parsers import csv_parser
from app.domains.imports.parsers.base import RawTxn

# ── Text-fallback patterns ────────────────────────────────────────────────────

# DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY, YYYY-MM-DD
_DATE_RE = re.compile(
    r"(?<!\d)(\d{2}[/\-\.]\d{2}[/\-\.]\d{4}|\d{4}[/\-\.]\d{2}[/\-\.]\d{2})(?!\d)"
)
# Signed amount at (or near) end of line, French or Anglo format.
# e.g. "-1 234,56", "1234.56", "(42,50)"
_AMT_RE = re.compile(
    r"(-?\(?\s*\d[\d\s ]*(?:[,\.]\d{1,2})?\)?)\s*(?:EUR|€)?\s*$"
)


def parse_pdf(content: bytes) -> list[RawTxn]:
    """Parse a PDF bank statement into canonical RawTxns."""
    with pdfplumber.open(BytesIO(content)) as pdf:
        txns = _from_tables(pdf)
        if txns:
            return txns
        return _from_text(pdf)


# ── Table extraction ──────────────────────────────────────────────────────────

def _from_tables(pdf: pdfplumber.PDF) -> list[RawTxn]:
    """Return RawTxns extracted from embedded table grids.

    Scans all pages for the first table whose header row matches ≥ 2 of our
    known column-name keywords.  Subsequent pages contribute data rows even
    if they no longer repeat the header.
    """
    headers: list[str] | None = None
    header_cols: dict[str, str | None] = {}
    all_rows: list[dict] = []

    for page in pdf.pages:
        for table in page.extract_tables():
            if not table:
                continue

            if headers is None:
                # Look for a header row anywhere in the first few rows.
                for hi, row in enumerate(table[:10]):
                    cells = [str(c or "").strip() for c in row]
                    cols = csv_parser.detect_columns(cells)
                    matched = sum(1 for v in cols.values() if v)
                    if matched >= 2:
                        headers = cells
                        header_cols = cols
                        for data_row in table[hi + 1:]:
                            all_rows.append(_zip(headers, data_row))
                        break
            else:
                # Headers already found — every row on subsequent pages is data.
                for data_row in table:
                    # Skip rows that look like a repeated header.
                    cells = [str(c or "").strip() for c in data_row]
                    cols = csv_parser.detect_columns(cells)
                    if sum(1 for v in cols.values() if v) >= 2:
                        continue  # repeated header row
                    all_rows.append(_zip(headers, data_row))

    if not all_rows or headers is None:
        return []

    dec_sep = _guess_decimal_sep(all_rows, header_cols)
    return csv_parser.build_txns(all_rows, header_cols, "%d/%m/%Y", dec_sep)


def _zip(headers: list[str], row: list) -> dict:
    return {headers[i]: str(c or "").strip() for i, c in enumerate(row) if i < len(headers)}


def _guess_decimal_sep(rows: list[dict], cols: dict) -> str:
    """Heuristic: if any amount cell contains a comma before the last 2 digits → ','."""
    amount_col = cols.get("amount") or cols.get("debit") or cols.get("credit")
    if not amount_col:
        return ","
    for row in rows[:20]:
        val = row.get(amount_col, "")
        if re.search(r",\d{2}$", val.strip()):
            return ","
        if re.search(r"\.\d{2}$", val.strip()):
            return "."
    return ","


# ── Text-line fallback ────────────────────────────────────────────────────────

def _from_text(pdf: pdfplumber.PDF) -> list[RawTxn]:
    """Last-resort: scan text lines for date + amount, extract description between."""
    txns: list[RawTxn] = []
    for page in pdf.pages:
        text = page.extract_text() or ""
        for line in text.splitlines():
            m_date = _DATE_RE.search(line)
            if not m_date:
                continue
            m_amt = _AMT_RE.search(line)
            if not m_amt:
                continue
            # Description: text between the date match and the amount match.
            desc_start = m_date.end()
            desc_end = m_amt.start()
            if desc_end <= desc_start:
                continue
            desc = line[desc_start:desc_end].strip(" |-")
            date_str = m_date.group(1)
            amt_str = m_amt.group(1)
            # Try both decimal separators; accept the one that gives a non-zero result.
            amount = Decimal("0")
            for sep in (",", "."):
                try:
                    amount = csv_parser.parse_amount(amt_str, sep)
                    if amount != Decimal("0"):
                        break
                except (InvalidOperation, ValueError):
                    continue
            if amount == Decimal("0"):
                continue
            try:
                date = csv_parser.parse_date(date_str, "%d/%m/%Y")
                txns.append(RawTxn(date=date, amount=amount, description=desc))
            except ValueError:
                continue
    return txns
