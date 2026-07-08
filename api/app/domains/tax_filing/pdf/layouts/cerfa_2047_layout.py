"""Form 2047 (foreign-source income) box layout — Feature J6
(docs/Backlog.md). Unlike 2042/3916's fixed box grid, 2047 needs one
row per `ForeignIncomeDeclaration` line, so the layout is built
dynamically from the number of lines rather than a fixed constant.
"""
from __future__ import annotations

from app.domains.tax_filing.pdf.box_grid import BoxPosition, FormLayout

_ROW_HEIGHT_MM = 12.0
_FIRST_ROW_Y_MM = 40.0


def build_2047_layout(num_lines: int) -> FormLayout:
    boxes: list[BoxPosition] = []
    for i in range(num_lines):
        y = _FIRST_ROW_Y_MM + i * _ROW_HEIGHT_MM
        boxes.append(BoxPosition(f"L{i + 1}-COUNTRY", "Pays", 20, y, 25))
        boxes.append(BoxPosition(f"L{i + 1}-DESC", "Origine du revenu", 47, y, 60))
        boxes.append(BoxPosition(f"L{i + 1}-AMOUNT", "Montant brut (EUR)", 109, y, 40))
        boxes.append(BoxPosition(f"L{i + 1}-METHOD", "Methode", 151, y, 44))
    return FormLayout(
        form_id="2047", title="Revenus de source etrangere", boxes=boxes
    )
