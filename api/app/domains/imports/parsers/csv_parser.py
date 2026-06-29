"""CSV statement parsing — delimiter/header detection, column heuristics, row→RawTxn.

This is the single source of truth for CSV column detection. The browser no
longer re-implements any of this (it previously kept a drifting copy of the
keyword lists, which is how ``"valeur"`` once matched ``"Date valeur"`` and
silently zeroed every amount).
"""
from __future__ import annotations

import csv
import datetime
import io
from decimal import Decimal, InvalidOperation

from app.domains.imports.parsers.base import RawTxn

# ── Column name heuristics (French + English bank CSVs) ─────────────────────
# Priority order matters: more specific / shorter names first so "date" beats
# "date valeur". Note: "valeur" is deliberately NOT an amount keyword — it
# matches "Date valeur".

_DATE_KW = [
    "date opération", "date de l'opération", "date operation",
    "date",                                   # simple "Date" column — before "date valeur"
    "datum",
    "date valeur", "date de valeur",          # value-date — lower priority
]
_AMT_KW = ["montant eur", "montant", "amount", "somme"]
_DEBIT_KW = ["débit euros", "débit", "debit", "dépense", "depense", "withdrawal", "debit amount"]
_CREDIT_KW = ["crédit euros", "crédit", "credit", "recette", "deposit", "credit amount"]
_DESC_KW = [
    "libellé opération", "libellé", "libelle",
    "intitulé de l'opération", "intitulé", "intitule",
    "description", "narration", "détail de l'écriture", "detail", "memo", "note",
]

_ALL_HEADER_KWS = _DATE_KW + _AMT_KW + _DEBIT_KW + _CREDIT_KW + _DESC_KW


def detect_delimiter(text: str) -> str:
    """Count delimiter occurrences across up to 20 lines to avoid metadata-row bias."""
    lines = [ln for ln in text.split("\n") if ln.strip()][:20]
    scores = {d: sum(ln.count(d) for ln in lines) for d in (";", ",", "\t")}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else ","


def find_header_row(lines: list[str], delimiter: str) -> int:
    """Return index of first line that contains ≥2 known column-name keywords.

    French bank exports often prepend 10-15 metadata rows (account holder name,
    balance, date range…) before the actual header row.
    """
    for i, line in enumerate(lines[:40]):
        cols = [c.strip().lower() for c in line.split(delimiter)]
        matches = sum(
            1 for c in cols
            if any(kw in c or c.startswith(kw) for kw in _ALL_HEADER_KWS)
        )
        if matches >= 2:
            return i
    return 0


def detect_columns(headers: list[str]) -> dict[str, str | None]:
    hl = {h.strip().lower(): h.strip() for h in headers}

    def find(kws: list[str]) -> str | None:
        for kw in kws:              # exact
            if kw in hl:
                return hl[kw]
        for kw in kws:              # starts-with
            for h in hl:
                if h.startswith(kw):
                    return hl[h]
        for kw in kws:              # contains
            for h in hl:
                if kw in h:
                    return hl[h]
        return None

    return {
        "date":        find(_DATE_KW),
        "amount":      find(_AMT_KW),
        "debit":       find(_DEBIT_KW),
        "credit":      find(_CREDIT_KW),
        "description": find(_DESC_KW),
    }


def parse_date(raw: str, fmt: str) -> datetime.date:
    raw = raw.strip()
    for f in [fmt, "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%m/%d/%Y", "%Y/%m/%d"]:
        try:
            return datetime.datetime.strptime(raw, f).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {raw!r}")


def parse_amount(raw: str, dec_sep: str) -> Decimal:
    s = raw.strip().replace("\xa0", "").replace(" ", "").replace(" ", "")
    if not s:
        return Decimal("0")
    negative = s.startswith("-") or (s.startswith("(") and s.endswith(")"))
    s = s.lstrip("+-").strip("()")
    if dec_sep == ",":
        s = s.replace(".", "").replace(",", ".")   # dot=thousands, comma=decimal
    else:
        s = s.replace(",", "")                      # comma=thousands, dot=decimal
    if not s:
        return Decimal("0")
    try:
        val = Decimal(s)
        return -val if negative else val
    except InvalidOperation:
        return Decimal("0")


def read_rows(
    text: str,
    delimiter: str | None = None,
    skip_rows: int | None = None,
) -> tuple[list[str], list[dict], str]:
    """Return ``(headers, rows, delimiter)`` after skipping metadata rows."""
    delimiter = delimiter or detect_delimiter(text)
    all_lines = [ln for ln in text.split("\n") if ln.strip()]
    if skip_rows is not None:
        header_idx = skip_rows
    else:
        header_idx = find_header_row(all_lines, delimiter)
    csv_text = "\n".join(all_lines[header_idx:])
    reader = csv.DictReader(io.StringIO(csv_text), delimiter=delimiter)
    rows = list(reader)
    headers = list(reader.fieldnames or [])
    return headers, rows, delimiter


def build_txns(
    rows: list[dict],
    cols: dict[str, str | None],
    date_format: str,
    decimal_separator: str,
) -> list[RawTxn]:
    """Turn raw CSV rows into canonical RawTxns using a resolved column map.

    ``cols`` keys: date, amount, debit, credit, description.
    """
    date_col = cols.get("date")
    amount_col = cols.get("amount")
    debit_col = cols.get("debit")
    credit_col = cols.get("credit")
    desc_col = cols.get("description")

    out: list[RawTxn] = []
    for row in rows:
        try:
            if not date_col:
                continue
            date_raw = (row.get(date_col) or "").strip()
            if not date_raw:
                continue
            txn_date = parse_date(date_raw, date_format)

            if amount_col and (row.get(amount_col) or "").strip():
                amount = parse_amount(row[amount_col], decimal_separator)
            elif debit_col or credit_col:
                debit = parse_amount(row.get(debit_col or "", ""), decimal_separator)
                credit = parse_amount(row.get(credit_col or "", ""), decimal_separator)
                amount = credit - debit            # credit = inflow (+), debit = outflow (−)
                if amount == Decimal("0"):
                    continue
            else:
                continue

            desc = (row.get(desc_col, "") if desc_col else "").strip()
            out.append(RawTxn(date=txn_date, amount=amount, description=desc))
        except (InvalidOperation, ValueError, KeyError):
            continue
    return out
