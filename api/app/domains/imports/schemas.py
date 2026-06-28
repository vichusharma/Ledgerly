"""Import domain schemas."""
from __future__ import annotations

import datetime

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
