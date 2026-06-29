"""CAMT.053 (ISO 20022) bank-statement parsing — hand-rolled, stdlib only.

CAMT.053 is XML with a versioned namespace (camt.053.001.02 / .04 / .08 …).
We ignore the namespace by matching on local tag names. Each ``<Ntry>`` is one
booked statement line:

    <Amt Ccy="EUR">123.45</Amt>     amount (always positive)
    <CdtDbtInd>CRDT|DBIT</CdtDbtInd> sign (CRDT = inflow +, DBIT = outflow −)
    <BookgDt><Dt>2026-05-16</Dt>     booking date (fallback: <ValDt>)
    <RmtInf><Ustrd>…</Ustrd>         remittance / description
"""
from __future__ import annotations

import datetime
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation

from app.domains.imports.parsers.base import RawTxn


def _local(tag: str) -> str:
    """Strip the ``{namespace}`` prefix ElementTree prepends to tags."""
    return tag.rsplit("}", 1)[-1]


def _find(elem: ET.Element, *names: str) -> ET.Element | None:
    """Depth-first search for the first descendant matching a local tag name."""
    for child in elem.iter():
        if _local(child.tag) in names:
            return child
    return None


def _text(elem: ET.Element | None) -> str:
    return (elem.text or "").strip() if elem is not None else ""


def _parse_date(raw: str) -> datetime.date | None:
    raw = raw.strip()[:10]   # may be a full dateTime; the date prefix is enough
    for f in ("%Y-%m-%d", "%d/%m/%Y", "%d.%m.%Y"):
        try:
            return datetime.datetime.strptime(raw, f).date()
        except ValueError:
            continue
    return None


def parse_camt(content: bytes) -> list[RawTxn]:
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return []

    txns: list[RawTxn] = []
    for ntry in root.iter():
        if _local(ntry.tag) != "Ntry":
            continue

        amt_el = _find(ntry, "Amt")
        try:
            amount = Decimal(_text(amt_el))
        except (InvalidOperation, ValueError):
            continue

        ind = _text(_find(ntry, "CdtDbtInd")).upper()
        if ind == "DBIT":
            amount = -amount

        # Booking date preferred, else value date.
        date = None
        for dt_holder in ("BookgDt", "ValDt"):
            holder = _find(ntry, dt_holder)
            if holder is not None:
                dt_el = _find(holder, "Dt", "DtTm")
                date = _parse_date(_text(dt_el))
                if date:
                    break
        if date is None:
            continue

        ustrd = _find(ntry, "Ustrd")
        desc = _text(ustrd) or _text(_find(ntry, "AddtlNtryInf"))

        txns.append(RawTxn(date=date, amount=amount, description=desc))
    return txns
