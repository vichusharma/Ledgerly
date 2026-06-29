"""Import domain schemas."""
from __future__ import annotations

import datetime
from decimal import Decimal

from pydantic import BaseModel


class ColumnMappingIn(BaseModel):
    institution: str
    column_map: dict[str, str]  # {"date": "Date", "amount": "Montant", ...}
    date_format: str = "%d/%m/%Y"
    decimal_separator: str = ","
    encoding: str = "utf-8"
    skip_rows: int = 0


class ImportMappingOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    institution: str
    column_map: dict
    date_format: str
    decimal_separator: str
    encoding: str
    skip_rows: int


class ImportBatchOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    account_id: int
    filename: str
    imported_at: datetime.datetime
    row_count: int
    duplicate_count: int
    is_rolled_back: bool


class SampleTxn(BaseModel):
    """A canonical preview transaction (used for self-describing formats)."""
    date: datetime.date
    amount: Decimal
    description: str


class StatementPreviewOut(BaseModel):
    """Preview response for any statement format — no DB write.

    For ``format == "csv"`` the ``headers``/``delimiter``/``detected`` fields
    drive the mapping UI. For OFX/QIF/CAMT they stay empty and ``sample_txns``
    holds the already-parsed canonical lines (no mapping needed).
    """
    format: str                              # "csv" | "ofx" | "qif" | "camt"
    headers: list[str] = []
    delimiter: str = ","
    detected: dict[str, str | None] = {}     # {"date": "Date opération", "amount": None, ...}
    preset_matched: bool = False             # a built-in bank preset was applied (CSV only)
    sample: list[dict] = []                  # CSV: first rows as dicts keyed by header
    sample_txns: list[SampleTxn] = []        # canonical preview of the first parsed lines


# Backwards-compatible alias (older imports referenced CsvPreviewOut).
CsvPreviewOut = StatementPreviewOut
