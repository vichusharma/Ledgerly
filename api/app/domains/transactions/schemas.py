"""Transactions domain schemas."""
from __future__ import annotations

import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CategoryCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    parent_id: int | None = None
    color: str | None = None


class CategoryOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    name: str
    parent_id: int | None
    color: str | None


class RuleCreateIn(BaseModel):
    pattern: str = Field(min_length=1, max_length=500, description="Python regex pattern")
    category_id: int
    account_id: int | None = None
    priority: int = 0


class RuleOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    pattern: str
    category_id: int
    account_id: int | None
    priority: int


class TransactionCreateIn(BaseModel):
    account_id: int
    date: datetime.date
    amount: Decimal
    currency: str = "EUR"
    description: str = ""
    category_id: int | None = None


class TransactionUpdateIn(BaseModel):
    category_id: int | None = None
    description: str | None = None
    vacation_budget_id: int | None = None


class SplitLine(BaseModel):
    amount: Decimal
    category_id: int | None = None
    description: str = ""


class TransactionSplitIn(BaseModel):
    splits: list[SplitLine] = Field(min_length=2)


class TransactionOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    account_id: int
    date: datetime.date
    amount: Decimal
    currency: str
    description: str
    category_id: int | None
    dedup_hash: str
    is_split: bool
    parent_id: int | None
    import_batch_id: int | None
