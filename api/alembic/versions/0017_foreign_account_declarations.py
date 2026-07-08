"""Add foreign_account_declarations table (Feature J2-S7, docs/Backlog.md)

Form 3916 foreign bank/financial account lines — one row per person per
tax year per account. `account_id` optionally links to an existing
Ledgerly `Account` (via `Account.country_code`, Feature J2-S6) when the
household also tracks it there; many lines won't have one.

Revision ID: 0017
Revises: 0016
Create Date: 2026-07-07
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "foreign_account_declarations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("person_id", sa.Integer(), sa.ForeignKey("persons.id"), nullable=False),
        sa.Column("tax_year", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=True),
        sa.Column("bank_name", sa.String(200), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=False),
        sa.Column("account_identifier_masked", sa.String(50), nullable=True),
        sa.Column(
            "opened_this_year", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "closed_this_year", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("foreign_account_declarations")
