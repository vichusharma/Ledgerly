"""QIF (Quicken Interchange Format) parsing — hand-rolled, stdlib only.

QIF is a simple line-oriented format. Each record ends with a line containing
only ``^``. Within a record the first character of each line is a field code:

    D  date            T/U  amount (signed)     P  payee
    M  memo            L    category            N  number/check

We only need date, amount and a description (payee, falling back to memo).
"""
from __future__ import annotations

import datetime
from decimal import Decimal, InvalidOperation

from app.domains.imports.parsers.base import RawTxn

_DATE_FORMATS = [
    "%d/%m/%Y", "%d/%m/%y", "%m/%d/%Y", "%m/%d/%y",
    "%Y-%m-%d", "%d.%m.%Y", "%d-%m-%Y",
]


def _parse_date(raw: str) -> datetime.date | None:
    raw = raw.strip().replace("'", "/").replace(" ", "")
    for f in _DATE_FORMATS:
        try:
            return datetime.datetime.strptime(raw, f).date()
        except ValueError:
            continue
    return None


def _parse_amount(raw: str) -> Decimal | None:
    s = raw.strip().replace("\xa0", "").replace(" ", "")
    if not s:
        return None
    # QIF amounts may use either separator depending on locale.
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")   # 1.234,56 → 1234.56
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def parse_qif(content: bytes) -> list[RawTxn]:
    text = content.decode("utf-8", errors="ignore")
    txns: list[RawTxn] = []
    cur: dict[str, str] = {}

    def flush() -> None:
        if not cur:
            return
        d = _parse_date(cur.get("D", ""))
        a = _parse_amount(cur.get("T") or cur.get("U") or "")
        if d is not None and a is not None:
            desc = (cur.get("P") or cur.get("M") or "").strip()
            txns.append(RawTxn(date=d, amount=a, description=desc))

    for line in text.splitlines():
        if not line:
            continue
        if line.startswith("!"):        # header / type directive
            continue
        if line.startswith("^"):        # end of record
            flush()
            cur = {}
            continue
        code, value = line[0], line[1:]
        # Keep the first occurrence of a code within a record.
        cur.setdefault(code, value)
    flush()                              # trailing record without a final "^"
    return txns
