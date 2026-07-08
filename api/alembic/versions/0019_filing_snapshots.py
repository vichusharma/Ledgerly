"""Add filing_snapshots table (Feature J5, docs/Backlog.md)

A lockable, stable per-year filing result — unlike `/tax/estimate`,
which is deliberately always recomputed fresh. Recomputing a locked
year is rejected (409) at the service layer; unlocking is explicit.

Revision ID: 0019
Revises: 0018
Create Date: 2026-07-07
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "filing_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tax_year", sa.Integer(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("locked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "computed_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint(
        "uq_filing_snapshots_tax_year", "filing_snapshots", ["tax_year"]
    )


def downgrade() -> None:
    op.drop_table("filing_snapshots")
