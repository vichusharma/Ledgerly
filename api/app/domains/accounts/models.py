"""Accounts domain models."""
from __future__ import annotations

import enum
from decimal import Decimal

import datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.db import Base


class AccountType(str, enum.Enum):
    bank = "bank"
    savings = "savings"
    investment_wrapper = "investment_wrapper"
    liability = "liability"


class WrapperType(str, enum.Enum):
    PEA = "PEA"
    PEA_PME = "PEA_PME"
    AV = "AV"           # Assurance Vie
    PER = "PER"
    PERO = "PERO"
    PERCO = "PERCO"
    PEE = "PEE"
    CTO = "CTO"         # Compte Titres Ordinaire
    LIVRET_A = "LIVRET_A"
    LDDS = "LDDS"
    LEP = "LEP"
    ESOP = "ESOP"
    OTHER = "OTHER"


class Household(Base):
    __tablename__ = "households"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    persons: Mapped[list["Person"]] = relationship("Person", back_populates="household")


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    household: Mapped["Household"] = relationship("Household", back_populates="persons")
    accounts: Mapped[list["Account"]] = relationship(
        "Account", foreign_keys="Account.owner_id", back_populates="owner"
    )


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[AccountType] = mapped_column(String(30), nullable=False)
    wrapper_type: Mapped[WrapperType | None] = mapped_column(
        String(20), nullable=True
    )
    institution: Mapped[str | None] = mapped_column(String(200), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)

    owner_id: Mapped[int] = mapped_column(ForeignKey("persons.id"), nullable=False)
    joint_owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("persons.id"), nullable=True
    )
    # What % of this account belongs to owner_id (rest belongs to joint_owner_id)
    ownership_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("100.00"), nullable=False
    )

    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    opened_at: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    owner: Mapped["Person"] = relationship(
        "Person", foreign_keys=[owner_id], back_populates="accounts"
    )
    joint_owner: Mapped["Person | None"] = relationship(
        "Person", foreign_keys=[joint_owner_id]
    )
