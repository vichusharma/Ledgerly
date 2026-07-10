"""Add accounts.manual_balance (manual balance override for savings accounts)

Lets a household enter a savings account's real balance directly (e.g. a
Livret A they don't want to import transactions for) instead of relying on
the summed-transactions calculation. When set, it overrides that calculation
in net worth for bank/savings accounts (see networth/service.py).

Revision ID: 0021
Revises: 0020
Create Date: 2026-07-10
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "accounts", sa.Column("manual_balance", sa.Numeric(20, 4), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("accounts", "manual_balance")
