"""Statement parsing layer — one canonical model across CSV/OFX/QIF/CAMT.053."""
from __future__ import annotations

from app.domains.imports.parsers import csv_parser, presets
from app.domains.imports.parsers.base import ParsedStatement, RawTxn
from app.domains.imports.parsers.camt_parser import parse_camt
from app.domains.imports.parsers.detect import detect_format
from app.domains.imports.parsers.ofx_parser import parse_ofx
from app.domains.imports.parsers.qif_parser import parse_qif

__all__ = [
    "ParsedStatement", "RawTxn", "csv_parser", "presets",
    "detect_format", "parse_non_csv",
]


def parse_non_csv(fmt: str, content: bytes) -> list[RawTxn]:
    """Parse a self-describing format (no column mapping needed)."""
    if fmt == "ofx":
        return parse_ofx(content)
    if fmt == "qif":
        return parse_qif(content)
    if fmt == "camt":
        return parse_camt(content)
    raise ValueError(f"Not a self-describing format: {fmt!r}")
