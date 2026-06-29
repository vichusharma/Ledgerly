"""Transactions domain models."""
from __future__ import annotations

import datetime
import hashlib
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.db import Base

# Association table — no ORM model needed (no extra columns).
transaction_labels = Table(
    "transaction_labels",
    Base.metadata,
    Column(
        "transaction_id", Integer,
        ForeignKey("transactions.id", ondelete="CASCADE"), primary_key=True,
    ),
    Column(
        "label_id", Integer,
        ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True,
    ),
)


class Label(Base):
    __tablename__ = "labels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#94a3b8")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id"), nullable=True
    )
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)  # hex

    parent: Mapped[Category | None] = relationship("Category", remote_side="Category.id")
    children: Mapped[list[Category]] = relationship("Category", back_populates="parent")


class CategoryRule(Base):
    __tablename__ = "category_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pattern: Mapped[str] = mapped_column(String(500), nullable=False)  # regex
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    account_id: Mapped[int | None] = mapped_column(
        ForeignKey("accounts.id"), nullable=True
    )  # None = applies to all accounts
    priority: Mapped[int] = mapped_column(Integer, default=0)

    category: Mapped[Category] = relationship("Category")


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    imported_at: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.utcnow, nullable=False
    )
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0)
    is_rolled_back: Mapped[bool] = mapped_column(Boolean, default=False)

    transactions: Mapped[list[Transaction]] = relationship(
        "Transaction", back_populates="import_batch"
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    import_batch_id: Mapped[int | None] = mapped_column(
        ForeignKey("import_batches.id"), nullable=True
    )

    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)  # negative = debit
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    description: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)

    # Dedup hash: sha256(account_id|date|amount|description)
    dedup_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    is_split: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("transactions.id"), nullable=True
    )

    # Vacation budget tag (P2)
    vacation_budget_id: Mapped[int | None] = mapped_column(
        ForeignKey("vacation_budgets.id"), nullable=True
    )

    # Recurring expense flag (P2)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurring_expense_id: Mapped[int | None] = mapped_column(
        ForeignKey("recurring_expenses.id"), nullable=True
    )

    import_batch: Mapped[ImportBatch | None] = relationship(
        "ImportBatch", back_populates="transactions"
    )
    category: Mapped[Category | None] = relationship("Category")
    splits: Mapped[list[Transaction]] = relationship(
        "Transaction", foreign_keys=[parent_id]
    )
    labels: Mapped[list[Label]] = relationship(
        "Label", secondary=transaction_labels, lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint("account_id", "dedup_hash", name="uq_txn_dedup"),
    )

    @staticmethod
    def compute_hash(account_id: int, date: datetime.date, amount: Decimal, description: str) -> str:
        raw = f"{account_id}|{date.isoformat()}|{amount}|{description}"
        return hashlib.sha256(raw.encode()).hexdigest()
