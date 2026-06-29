"""Canonical statement model shared by every format parser."""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class RawTxn:
    """A single statement line, normalised across all formats.

    ``amount`` is signed: inflow positive, outflow negative.
    """
    date: datetime.date
    amount: Decimal
    description: str


@dataclass
class ParsedStatement:
    """Result of parsing an uploaded file.

    For self-describing formats (OFX/QIF/CAMT) ``txns`` is fully populated and
    the CSV-mapping fields stay empty. For CSV, ``headers`` / ``detected`` /
    ``sample`` describe the column layout so the UI can render a mapping step;
    ``txns`` is filled only at import time once columns are resolved.
    """
    format: str                                   # "csv" | "ofx" | "qif" | "camt"
    txns: list[RawTxn] = field(default_factory=list)
    headers: list[str] = field(default_factory=list)
    detected: dict[str, str | None] = field(default_factory=dict)
    sample: list[dict] = field(default_factory=list)
