"""Shared helper for unit tests that need a real (synthetic) PDF to
exercise a parser's pdfplumber wiring end-to-end, not just its regex
helpers in isolation."""
from __future__ import annotations

from io import BytesIO

from reportlab.pdfgen import canvas


def make_text_pdf(lines: list[str]) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(600, 800))
    y = 750
    for line in lines:
        c.drawString(50, y, line)
        y -= 20
    c.save()
    return buf.getvalue()
