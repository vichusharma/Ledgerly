"""Investments domain schemas."""
from __future__ import annotations

import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.domains.investments.models import AssetClass, LotType


class InstrumentCreateIn(BaseModel):
    isin: str | None = None
    ticker: str | None = None
    name: str
    asset_class: AssetClass = AssetClass.equity
    region: str | None = None
    currency: str = "EUR"


class InstrumentOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    isin: str | None
    ticker: str | None
    name: str
    asset_class: AssetClass
    region: str | None
    currency: str


class LotCreateIn(BaseModel):
    account_id: int
    instrument_id: int | None = None
    lot_type: LotType
    quantity: Decimal
    price: Decimal
    fees: Decimal = Decimal("0")
    currency: str = "EUR"
    settled_at: datetime.date
    notes: str | None = None


class LotOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    account_id: int
    instrument_id: int | None
    lot_type: LotType
    quantity: Decimal
    price: Decimal
    fees: Decimal
    currency: str
    settled_at: datetime.date
    notes: str | None


class PriceCreateIn(BaseModel):
    instrument_id: int
    date: datetime.date
    close: Decimal
    currency: str = "EUR"


class PriceOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    instrument_id: int
    date: datetime.date
    close: Decimal
    currency: str


class PerformanceSeriesPoint(BaseModel):
    date: datetime.date
    value: Decimal


class PerformanceOut(BaseModel):
    twr: float | None
    xirr: float | None
    total_invested: Decimal
    current_value: Decimal
    total_gain: Decimal
    gain_pct: float
    series: list[PerformanceSeriesPoint]


class AllocationSliceOut(BaseModel):
    asset_class: str
    market_value: Decimal
    actual_pct: Decimal
    target_pct: Decimal
    drift_pct: Decimal


class AllocationOut(BaseModel):
    total_value: Decimal
    by_class: list[AllocationSliceOut]
    by_region: list[AllocationSliceOut]
    by_wrapper: list[AllocationSliceOut]


class TargetAllocationIn(BaseModel):
    allocations: list[dict[str, object]]  # [{"asset_class": "equity", "target_pct": 70}]
