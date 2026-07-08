"""Form 3916 (foreign bank accounts) box layout — Feature J6
(docs/Backlog.md). Same dynamic-rows approach as `cerfa_2047_layout.py`
— one row per `ForeignAccountDeclaration` line.
"""
from __future__ import annotations

from app.domains.tax_filing.pdf.box_grid import BoxPosition, FormLayout

_ROW_HEIGHT_MM = 12.0
_FIRST_ROW_Y_MM = 40.0


def build_3916_layout(num_lines: int) -> FormLayout:
    boxes: list[BoxPosition] = []
    for i in range(num_lines):
        y = _FIRST_ROW_Y_MM + i * _ROW_HEIGHT_MM
        boxes.append(BoxPosition(f"L{i + 1}-BANK", "Banque", 20, y, 55))
        boxes.append(BoxPosition(f"L{i + 1}-COUNTRY", "Pays", 77, y, 25))
        boxes.append(BoxPosition(f"L{i + 1}-ACCOUNT", "N. compte (masque)", 104, y, 50))
        boxes.append(BoxPosition(f"L{i + 1}-STATUS", "Statut", 156, y, 39))
    return FormLayout(
        form_id="3916", title="Comptes detenus a l'etranger", boxes=boxes
    )
