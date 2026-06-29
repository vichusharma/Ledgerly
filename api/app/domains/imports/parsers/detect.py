"""Detect a statement file's format from its name and content."""
from __future__ import annotations

import os

Format = str  # "csv" | "ofx" | "qif" | "camt" | "pdf"


def _sniff(text: str) -> Format | None:
    head = text.lstrip()[:4000].upper()
    if "<DOCUMENT" in head and "CAMT.05" in head:
        return "camt"
    if "<NTRY>" in head or "URN:ISO:STD:ISO:20022" in head:
        return "camt"
    if "OFXHEADER" in head or "<OFX>" in head:
        return "ofx"
    if head.startswith("!TYPE:") or "\n!TYPE:" in head:
        return "qif"
    return None


def detect_format(filename: str | None, content: bytes) -> Format:
    """Best-effort format detection: extension first, then a content sniff.

    Falls back to ``"csv"`` since that is the only format that has a manual
    mapping safety net in the UI.
    """
    ext = os.path.splitext(filename or "")[1].lower().lstrip(".")
    if ext == "pdf":
        return "pdf"
    if ext in ("ofx", "qfx"):
        return "ofx"
    if ext == "qif":
        return "qif"
    if ext in ("xml", "camt"):
        # Could be CAMT or unrelated XML — confirm by sniffing.
        sniffed = _sniff(_decode(content))
        return sniffed or "csv"
    if ext in ("csv", "txt", "tsv"):
        # Some banks hand out OFX/QIF with a .txt extension — sniff to be safe.
        sniffed = _sniff(_decode(content))
        return sniffed or "csv"

    # Unknown extension: rely entirely on content.
    return _sniff(_decode(content)) or "csv"


def _decode(content: bytes) -> str:
    for enc in ("utf-8", "latin-1"):
        try:
            return content.decode(enc)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="ignore")
