"""ESPP purchase confirmation PDF parser — Feature J2-S2 (docs/Backlog.md).

See `parsers/_common.py` for the "no real sample yet" caveat shared by
every Epic J document parser.
"""
from __future__ import annotations

from io import BytesIO

import pdfplumber

from app.domains.tax_filing.parsers._common import (
    find_labeled_amount,
    find_labeled_date,
    find_labeled_percent,
    find_labeled_shares,
)
from app.domains.tax_filing.schemas import EsppPurchasePreviewOut

_PURCHASE_DATE_LABELS = ("Purchase Date", "Date d'achat")
_SHARES_LABELS = ("Shares Purchased", "Number of Shares", "Actions achetees")
_PURCHASE_PRICE_LABELS = ("Purchase Price", "Prix d'achat")
_FMV_LABELS = ("Fair Market Value", "FMV at Purchase", "Juste valeur")
_DISCOUNT_LABELS = ("Discount", "Discount Rate", "Remise")


def parse_pdf_espp_purchase(content: bytes) -> EsppPurchasePreviewOut:
    with pdfplumber.open(BytesIO(content)) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    return EsppPurchasePreviewOut(
        purchase_date=find_labeled_date(text, _PURCHASE_DATE_LABELS),
        shares=find_labeled_shares(text, _SHARES_LABELS),
        purchase_price=find_labeled_amount(text, _PURCHASE_PRICE_LABELS),
        fmv_at_purchase=find_labeled_amount(text, _FMV_LABELS),
        discount_pct=find_labeled_percent(text, _DISCOUNT_LABELS),
    )
