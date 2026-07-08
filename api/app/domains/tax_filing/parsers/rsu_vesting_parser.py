"""RSU vest confirmation PDF parser — Feature J2-S1 (docs/Backlog.md).

See `parsers/_common.py` for the "no real sample yet" caveat shared by
every Epic J document parser.
"""
from __future__ import annotations

from io import BytesIO

import pdfplumber

from app.domains.tax_filing.parsers._common import (
    find_labeled_amount,
    find_labeled_date,
    find_labeled_int,
    find_labeled_shares,
)
from app.domains.tax_filing.schemas import RsuVestingPreviewOut

_GRANT_DATE_LABELS = ("Grant Date", "Date d'attribution")
_VEST_DATE_LABELS = ("Vest Date", "Vesting Date", "Date d'acquisition")
_TOTAL_SHARES_LABELS = ("Total Shares Granted", "Total Shares", "Nombre total d'actions")
_VESTED_SHARES_LABELS = ("Shares Vested", "Vested Shares", "Actions acquises")
_GRANT_PRICE_LABELS = ("Grant Price", "Prix d'attribution")
_FMV_LABELS = ("Fair Market Value", "FMV at Vest", "Juste valeur")
_CLIFF_LABELS = ("Cliff", "Cliff Period", "Periode de cliff")
_VESTING_PERIOD_LABELS = ("Vesting Period", "Vesting Term", "Duree d'acquisition")


def parse_pdf_rsu_vesting(content: bytes) -> RsuVestingPreviewOut:
    with pdfplumber.open(BytesIO(content)) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    return RsuVestingPreviewOut(
        grant_date=find_labeled_date(text, _GRANT_DATE_LABELS),
        total_shares=find_labeled_shares(text, _TOTAL_SHARES_LABELS),
        cliff_months=find_labeled_int(text, _CLIFF_LABELS),
        vesting_months=find_labeled_int(text, _VESTING_PERIOD_LABELS),
        grant_price=find_labeled_amount(text, _GRANT_PRICE_LABELS),
        vest_date=find_labeled_date(text, _VEST_DATE_LABELS),
        vested_shares=find_labeled_shares(text, _VESTED_SHARES_LABELS),
        vest_fmv=find_labeled_amount(text, _FMV_LABELS),
    )
