"""Transactions domain schemas."""
from __future__ import annotations

import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class LabelCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    color: str = "#94a3b8"


class LabelOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    name: str
    color: str


class TransactionLabelIn(BaseModel):
    label_ids: list[int]


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


class LabelUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    color: str | None = None


class LabelRuleCreateIn(BaseModel):
    pattern: str = Field(min_length=1, max_length=500, description="Python regex pattern")
    label_id: int
    priority: int = 0


class LabelRuleOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    pattern: str
    label_id: int
    priority: int


class LabelWithRuleIn(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    color: str = "#94a3b8"
    patterns: list[str] = []


class BulkLabelsIn(BaseModel):
    labels: list[LabelWithRuleIn]


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
    labels: list[LabelOut] = []


# ── Analytics ─────────────────────────────────────────────────────────────────

class MonthBucket(BaseModel):
    month: str            # "YYYY-MM"
    spent: Decimal        # positive magnitude of debits
    income: Decimal       # positive magnitude of credits


class CategoryBucket(BaseModel):
    category_id: int | None
    name: str
    color: str | None
    spent: Decimal
    pct: float            # share of total spent, 0–100


class LabelBucket(BaseModel):
    label_id: int | None
    name: str
    color: str | None
    spent: Decimal
    pct: float            # share of total spent, 0–100 (labels overlap, so totals may exceed 100)


class MerchantBucket(BaseModel):
    merchant: str
    spent: Decimal
    count: int


class RerunRulesOut(BaseModel):
    scanned: int
    categorized: int
    labeled: int


class AnalyticsOut(BaseModel):
    total_spent: Decimal
    total_income: Decimal
    net: Decimal
    txn_count: int
    by_month: list[MonthBucket] = []
    by_category: list[CategoryBucket] = []
    by_label: list[LabelBucket] = []
    top_merchants: list[MerchantBucket] = []
