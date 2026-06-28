"""Investments domain models."""
from __future__ import annotations

import enum
from decimal import Decimal

import datetime

from sqlalchemy import (
    Date, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.db import Base


class AssetClass(str, enum.Enum):
    equity = "equity"
    bond = "bond"
    cash = "cash"
    real_estate = "real_estate"
    commodity = "commodity"
    crypto = "crypto"
    other = "other"


class LotType(str, enum.Enum):
    buy = "buy"
    sell = "sell"
    dividend = "dividend"
    contribution = "contribution"  # cash in (for AV/PER)
    withdrawal = "withdrawal"      # cash out
    fee = "fee"
    split = "split"                # stock split
    vesting = "vesting"            # RSU vest


class WrapperType(str, enum.Enum):
    PEA = "PEA"
    PEA_PME = "PEA_PME"
    AV = "AV"
    PER = "PER"
    PERO = "PERO"
    PERCO = "PERCO"
    PEE = "PEE"
    CTO = "CTO"
    LIVRET_A = "LIVRET_A"
    LDDS = "LDDS"
    LEP = "LEP"
    ESOP = "ESOP"
    OTHER = "OTHER"


class Instrument(Base):
    __tablename__ = "instruments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    isin: Mapped[str | None] = mapped_column(String(12), nullable=True, unique=True)
    ticker: Mapped[str | None] = mapped_column(String(20), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    asset_class: Mapped[AssetClass] = mapped_column(
        Enum(AssetClass), default=AssetClass.equity
    )
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")

    lots: Mapped[list["InvestmentLot"]] = relationship("InvestmentLot", back_populates="instrument")
    prices: Mapped[list["InstrumentPrice"]] = relationship(
        "InstrumentPrice", back_populates="instrument"
    )


class InstrumentPrice(Base):
    """End-of-day closing price."""
    __tablename__ = "instrument_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")

    instrument: Mapped["Instrument"] = relationship("Instrument", back_populates="prices")

    __table_args__ = (
        UniqueConstraint("instrument_id", "date", name="uq_price_instrument_date"),
    )


class InvestmentLot(Base):
    __tablename__ = "investment_lots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    instrument_id: Mapped[int | None] = mapped_column(
        ForeignKey("instruments.id"), nullable=True
    )  # None for cash contributions/withdrawals

    lot_type: Mapped[LotType] = mapped_column(Enum(LotType), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    fees: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=Decimal("0"))
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    settled_at: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ESOP/RSU vesting fields (P2)
    vesting_schedule_id: Mapped[int | None] = mapped_column(
        ForeignKey("vesting_schedules.id"), nullable=True
    )

    instrument: Mapped["Instrument | None"] = relationship(
        "Instrument", back_populates="lots"
    )


class TargetAllocation(Base):
    """User-defined target allocation per asset class."""
    __tablename__ = "target_allocations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_class: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    target_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)


class VestingSchedule(Base):
    """ESOP/RSU vesting schedule (P2)."""
    __tablename__ = "vesting_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    grant_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    total_shares: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    cliff_months: Mapped[int] = mapped_column(Integer, default=12)
    vesting_months: Mapped[int] = mapped_column(Integer, default=48)
    grant_price: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
