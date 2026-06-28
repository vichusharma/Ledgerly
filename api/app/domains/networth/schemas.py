"""Net worth schemas."""
from __future__ import annotations

import datetime
from decimal import Decimal

from pydantic import BaseModel


class NetWorthBreakdown(BaseModel):
    assets: Decimal
    liabilities: Decimal
    net_worth: Decimal


class NetWorthOut(BaseModel):
    current: Decimal
    assets: Decimal
    liabilities: Decimal
    by_person: dict[str, NetWorthBreakdown]


class NetWorthSeriesOut(BaseModel):
    date: datetime.date
    net_worth: Decimal
    assets: Decimal
    liabilities: Decimal
