"""Foreign bank statement PDF parser — Feature J2-S4 (docs/Backlog.md).

See `parsers/_common.py` for the "no real sample yet" caveat shared by
every Epic J document parser. `country_code` is deliberately never
guessed from free text — always left for the user to pick in the
review step. The account number is masked to its last 4 characters
even in the preview (never surfaced or stored in full) since a bank
statement PDF often shows the complete number.
"""
from __future__ import annotations

import re
from io import BytesIO

import pdfplumber

from app.domains.tax_filing.parsers._common import find_labeled_value
from app.domains.tax_filing.schemas import ForeignAccountPreviewOut

_BANK_NAME_LABELS = ("Bank", "Bank Name", "Institution", "Banque")
_ACCOUNT_NUMBER_LABELS = ("Account Number", "IBAN", "Numero de compte")
_OPENED_RE = re.compile(r"account opened|nouveau compte|compte ouvert", re.IGNORECASE)
_CLOSED_RE = re.compile(r"account closed|compte cloture|compte ferme", re.IGNORECASE)


def _mask_account_number(raw: str | None) -> str | None:
    if not raw:
        return None
    digits_and_letters = re.sub(r"\s+", "", raw)
    if len(digits_and_letters) <= 4:
        return digits_and_letters
    return f"****{digits_and_letters[-4:]}"


def parse_pdf_foreign_bank_statement(content: bytes) -> ForeignAccountPreviewOut:
    with pdfplumber.open(BytesIO(content)) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    return ForeignAccountPreviewOut(
        bank_name=find_labeled_value(text, _BANK_NAME_LABELS),
        country_code=None,
        account_identifier_masked=_mask_account_number(
            find_labeled_value(text, _ACCOUNT_NUMBER_LABELS)
        ),
        opened_this_year=bool(_OPENED_RE.search(text)) or None,
        closed_this_year=bool(_CLOSED_RE.search(text)) or None,
    )
