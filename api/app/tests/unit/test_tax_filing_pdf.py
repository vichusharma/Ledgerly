"""Unit tests — Cerfa-facsimile PDF generation (Feature J6, docs/Backlog.md).

Checks structural correctness (valid PDF bytes, right number of boxes/
rows, disclaimer present) — not visual fidelity, since there's no
official government asset to compare against (the riskiest/most-
ambitious feature per the backlog, flagged as inherently iterative).
"""
from __future__ import annotations

from app.domains.tax_filing.pdf.box_grid import BoxPosition, FormLayout, render_box_grid
from app.domains.tax_filing.pdf.generator import (
    generate_2042_pdf,
    generate_2047_pdf,
    generate_3916_pdf,
)
from app.domains.tax_filing.pdf.layouts.cerfa_2047_layout import build_2047_layout
from app.domains.tax_filing.pdf.layouts.cerfa_3916_layout import build_3916_layout


def test_render_box_grid_produces_valid_pdf_bytes():
    layout = FormLayout(
        form_id="TEST", title="Test Form",
        boxes=[BoxPosition("1AA", "Test box", 20, 40, 80)],
    )
    pdf_bytes = render_box_grid(layout, {"1AA": "1234.56"})
    assert pdf_bytes.startswith(b"%PDF")
    assert b"%%EOF" in pdf_bytes


def test_build_2047_layout_one_row_per_line():
    layout = build_2047_layout(3)
    # 4 boxes per row (country/desc/amount/method)
    assert len(layout.boxes) == 12
    assert layout.boxes[0].code == "L1-COUNTRY"
    assert layout.boxes[-1].code == "L3-METHOD"


def test_build_2047_layout_zero_lines_is_empty():
    layout = build_2047_layout(0)
    assert layout.boxes == []


def test_build_3916_layout_one_row_per_line():
    layout = build_3916_layout(2)
    assert len(layout.boxes) == 8
    assert layout.boxes[0].code == "L1-BANK"


def test_generate_2042_pdf_from_payload():
    payload = {
        "boxes_2042": [
            {"code": "1AJ", "label": "Salaires", "amount": "50000.00"},
        ],
    }
    pdf_bytes = generate_2042_pdf(payload)
    assert pdf_bytes.startswith(b"%PDF")


def test_generate_2047_pdf_from_payload_with_lines():
    payload = {
        "lines_2047": [
            {
                "source_country_code": "IN", "source_description": "Infosys",
                "gross_amount_eur": "200.00", "elimination_method": "credit_equal_to_french_tax",
                "simplification_keys": [], "french_tax_credit_or_exemption": "30.00",
            },
        ],
    }
    pdf_bytes = generate_2047_pdf(payload)
    assert pdf_bytes.startswith(b"%PDF")


def test_generate_2047_pdf_no_lines_still_produces_valid_pdf():
    pdf_bytes = generate_2047_pdf({"lines_2047": []})
    assert pdf_bytes.startswith(b"%PDF")


def test_generate_3916_pdf_from_payload_with_entries():
    payload = {
        "entries_3916": [
            {
                "bank_name": "State Bank of India", "country_code": "IN",
                "account_identifier_masked": "****3456",
                "opened_this_year": True, "closed_this_year": False,
            },
        ],
    }
    pdf_bytes = generate_3916_pdf(payload)
    assert pdf_bytes.startswith(b"%PDF")
