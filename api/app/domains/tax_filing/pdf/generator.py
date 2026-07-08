"""Generates 2042/2047/3916 PDFs from a `FilingSnapshot.payload` dict —
Feature J6 (docs/Backlog.md). See `box_grid.py`'s module docstring for
the facsimile-not-official-form caveat.
"""
from __future__ import annotations

from app.domains.tax_filing.pdf.box_grid import render_box_grid
from app.domains.tax_filing.pdf.layouts.cerfa_2042_layout import LAYOUT_2042
from app.domains.tax_filing.pdf.layouts.cerfa_2047_layout import build_2047_layout
from app.domains.tax_filing.pdf.layouts.cerfa_3916_layout import build_3916_layout


def generate_2042_pdf(payload: dict) -> bytes:
    values = {box["code"]: str(box["amount"]) for box in payload["boxes_2042"]}
    return render_box_grid(LAYOUT_2042, values)


def generate_2047_pdf(payload: dict) -> bytes:
    lines = payload["lines_2047"]
    layout = build_2047_layout(len(lines))
    values: dict[str, str] = {}
    for i, line in enumerate(lines):
        n = i + 1
        values[f"L{n}-COUNTRY"] = line["source_country_code"]
        values[f"L{n}-DESC"] = line["source_description"]
        values[f"L{n}-AMOUNT"] = str(line["gross_amount_eur"])
        values[f"L{n}-METHOD"] = line["elimination_method"]
    return render_box_grid(layout, values)


def generate_3916_pdf(payload: dict) -> bytes:
    entries = payload["entries_3916"]
    layout = build_3916_layout(len(entries))
    values: dict[str, str] = {}
    for i, entry in enumerate(entries):
        n = i + 1
        values[f"L{n}-BANK"] = entry["bank_name"]
        values[f"L{n}-COUNTRY"] = entry["country_code"]
        values[f"L{n}-ACCOUNT"] = entry.get("account_identifier_masked") or ""
        status_parts = []
        if entry["opened_this_year"]:
            status_parts.append("Ouvert")
        if entry["closed_this_year"]:
            status_parts.append("Clos")
        values[f"L{n}-STATUS"] = "/".join(status_parts) or "-"
    return render_box_grid(layout, values)
