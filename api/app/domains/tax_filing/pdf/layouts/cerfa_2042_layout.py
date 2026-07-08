"""Form 2042 (main return) box layout — Feature J6 (docs/Backlog.md).

Fixed grid: salary boxes (1AJ/1BJ, per Feature J4's
`map_estimate_to_2042_boxes`) and investment-income boxes (2DC/2CK,
per `map_investment_income_to_2042_boxes`). Representative positions,
not verified against the current-year official form — see
`pdf/box_grid.py`'s module docstring.
"""
from __future__ import annotations

from app.domains.tax_filing.pdf.box_grid import BoxPosition, FormLayout

LAYOUT_2042 = FormLayout(
    form_id="2042",
    title="Declaration des revenus",
    boxes=[
        BoxPosition("1AJ", "Traitements et salaires (declarant 1)", 20, 40, 85),
        BoxPosition("1BJ", "Traitements et salaires (declarant 2)", 110, 40, 85),
        BoxPosition("2DC", "Revenus des valeurs mobilieres (bareme)", 20, 55, 85),
        BoxPosition("2CK", "Revenus des valeurs mobilieres (PFU)", 110, 55, 85),
    ],
)
