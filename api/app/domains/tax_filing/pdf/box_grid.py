"""Generic Cerfa-style box-grid PDF renderer — Feature J6 (docs/Backlog.md).

**This is a structural recreation, not a copy of DGFiP's actual
template.** A true pixel-identical copy of the official Cerfa 2042/
2047/3916 forms isn't legally reproducible (copyrighted, changes
yearly) — this draws a programmatic box grid (box code + label + value)
via `reportlab`, with a disclaimer footer stamped on every page. Box
codes and positions are representative, not verified against the
actual current-year DGFiP instructions (a documented simplification —
see docs/Backlog.md) — they must be checked before this is ever used
for a real filing.

One generic renderer reused across all three forms — layouts are pure
data (`FormLayout`/`BoxPosition`), so next year's box renumbering is a
data edit here, mirroring `TaxYearConfig`'s JSONB-brackets philosophy
for `core/tax.py`'s barème.
"""
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

DISCLAIMER = (
    "Document genere par Ledgerly -- reproduction structurelle, non un formulaire "
    "officiel Cerfa. Verifier les codes de case et la mise en page aupres de la "
    "documentation DGFiP en vigueur avant tout depot."
)


@dataclass(frozen=True)
class BoxPosition:
    code: str
    label: str
    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float = 10.0


@dataclass(frozen=True)
class FormLayout:
    form_id: str
    title: str
    boxes: list[BoxPosition]


def render_box_grid(layout: FormLayout, values: dict[str, str]) -> bytes:
    """Draws one page: a title, one labeled+bordered box per layout
    entry (box code, label, and its value if present in `values`), and
    the facsimile disclaimer footer. Returns this one form's PDF bytes.
    """
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    _, page_height = A4

    c.setFont("Helvetica-Bold", 14)
    c.drawString(20 * mm, page_height - 20 * mm, f"{layout.form_id} -- {layout.title}")

    for box in layout.boxes:
        x = box.x_mm * mm
        top = page_height - box.y_mm * mm
        w = box.width_mm * mm
        h = box.height_mm * mm
        c.rect(x, top - h, w, h)

        c.setFont("Helvetica", 6)
        c.drawString(x + 1 * mm, top - 4 * mm, box.code)
        c.drawString(x + 1 * mm, top - h + 2 * mm, box.label[:45])

        value = values.get(box.code)
        if value:
            c.setFont("Helvetica-Bold", 8)
            c.drawRightString(x + w - 1 * mm, top - 4 * mm, str(value))

    c.setFont("Helvetica-Oblique", 6)
    c.drawString(20 * mm, 12 * mm, DISCLAIMER[:150])
    c.drawString(20 * mm, 8 * mm, DISCLAIMER[150:])
    c.showPage()
    c.save()
    return buf.getvalue()
