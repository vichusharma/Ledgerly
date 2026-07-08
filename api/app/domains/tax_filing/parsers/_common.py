"""Shared regex helpers for Epic J's foreign-document parsers.

No real sample document was available for any of these four document
types (RSU vesting confirmations, ESPP purchase confirmations, foreign
dividend statements, foreign bank statements) — built generically first
against plausible English/French equity-plan and bank-statement
vocabulary, same approach `pdf_payslip_parser.py` started from before
being tuned against a real sample. Every extracted field is nullable
and reviewed/corrected by the user before anything is saved.
"""
from __future__ import annotations

import datetime
import re
from decimal import Decimal, InvalidOperation

_DATE_PATTERNS = (
    # 2026-01-15
    (re.compile(r"(\d{4})-(\d{2})-(\d{2})"), lambda m: (int(m[1]), int(m[2]), int(m[3]))),
    # 01/15/2026 or 15/01/2026 — ambiguous; treated as MM/DD/YYYY since
    # these plan-statement formats are predominantly US-broker-issued.
    (
        re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})"),
        lambda m: (int(m[3]), int(m[1]), int(m[2])),
    ),
)

_AMOUNT_RE = re.compile(r"[\$€]?\s?(-?[\d,]+\.\d{2})")
_PERCENT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%")
_SHARES_RE = re.compile(r"(-?[\d,]+(?:\.\d+)?)")


def find_labeled_value(text: str, labels: tuple[str, ...]) -> str | None:
    """Return the text following the first matching "Label: value" line,
    e.g. label "Grant Date" matches "Grant Date: 01/15/2026" -> "01/15/2026".
    The colon is deliberately mandatory (not optional) — a short generic
    label like "Bank" would otherwise false-match inside an unrelated
    title line like "Bank Statement"."""
    for label in labels:
        m = re.search(rf"{re.escape(label)}\s*:\s*([^\n]+)", text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def parse_date(raw: str | None) -> datetime.date | None:
    if not raw:
        return None
    for pattern, to_ymd in _DATE_PATTERNS:
        m = pattern.search(raw)
        if m:
            try:
                year, month, day = to_ymd(m)
                return datetime.date(year, month, day)
            except ValueError:
                continue
    return None


def parse_amount(raw: str | None) -> Decimal | None:
    if not raw:
        return None
    m = _AMOUNT_RE.search(raw.replace(",", ""))
    if not m:
        return None
    try:
        return Decimal(m.group(1))
    except InvalidOperation:
        return None


def parse_percent(raw: str | None) -> Decimal | None:
    if not raw:
        return None
    m = _PERCENT_RE.search(raw)
    if not m:
        return None
    try:
        return Decimal(m.group(1))
    except InvalidOperation:
        return None


def parse_shares(raw: str | None) -> Decimal | None:
    if not raw:
        return None
    m = _SHARES_RE.search(raw.replace(",", ""))
    if not m:
        return None
    try:
        return Decimal(m.group(1))
    except InvalidOperation:
        return None


def parse_int(raw: str | None) -> int | None:
    if not raw:
        return None
    m = re.search(r"\d+", raw)
    return int(m.group()) if m else None


def find_labeled_date(text: str, labels: tuple[str, ...]) -> datetime.date | None:
    return parse_date(find_labeled_value(text, labels))


def find_labeled_amount(text: str, labels: tuple[str, ...]) -> Decimal | None:
    return parse_amount(find_labeled_value(text, labels))


def find_labeled_percent(text: str, labels: tuple[str, ...]) -> Decimal | None:
    return parse_percent(find_labeled_value(text, labels))


def find_labeled_shares(text: str, labels: tuple[str, ...]) -> Decimal | None:
    return parse_shares(find_labeled_value(text, labels))


def find_labeled_int(text: str, labels: tuple[str, ...]) -> int | None:
    return parse_int(find_labeled_value(text, labels))
