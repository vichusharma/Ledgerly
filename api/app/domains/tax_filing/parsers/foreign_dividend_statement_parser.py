"""Foreign dividend statement PDF parser — Feature J2-S3 (docs/Backlog.md).

See `parsers/_common.py` for the "no real sample yet" caveat shared by
every Epic J document parser. `source_country_code` is deliberately
never guessed from free text (too error-prone) — always left for the
user to pick in the review step.
"""
from __future__ import annotations

from io import BytesIO

import pdfplumber

from app.domains.tax_filing.parsers._common import (
    find_labeled_amount,
    find_labeled_date,
    find_labeled_value,
)
from app.domains.tax_filing.schemas import ForeignIncomePreviewOut

_PAYER_LABELS = ("Payer", "Issuer", "Company", "Emetteur")
_GROSS_LABELS = ("Gross Dividend", "Gross Amount", "Dividende brut")
_TAX_WITHHELD_LABELS = (
    "Tax Withheld", "Withholding Tax", "Foreign Tax Paid", "Impot retenu",
)
_PAYMENT_DATE_LABELS = ("Payment Date", "Date de paiement")


def parse_pdf_foreign_dividend_statement(content: bytes) -> ForeignIncomePreviewOut:
    with pdfplumber.open(BytesIO(content)) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    return ForeignIncomePreviewOut(
        # Never guessed from free text — too error-prone; always picked
        # by the user in the review step.
        source_country_code=None,
        source_description=find_labeled_value(text, _PAYER_LABELS),
        gross_amount_eur=find_labeled_amount(text, _GROSS_LABELS),
        foreign_tax_paid_eur=find_labeled_amount(text, _TAX_WITHHELD_LABELS),
        income_date=find_labeled_date(text, _PAYMENT_DATE_LABELS),
    )
