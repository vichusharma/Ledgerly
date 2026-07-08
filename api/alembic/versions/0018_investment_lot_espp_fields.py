"""Add investment_lots.fmv_at_acquisition / discount_pct (ESPP, J2-S2)

Nullable columns only relevant to ESPP-purchase lots (`lot_type=buy`);
every other lot type leaves them null. See docs/Backlog.md Feature
J2-S2 — modeled as extra columns rather than a distinct LotType since
position/cost-basis math already treats an ESPP purchase like any
other buy.

Revision ID: 0018
Revises: 0017
Create Date: 2026-07-07
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "investment_lots", sa.Column("fmv_at_acquisition", sa.Numeric(20, 6), nullable=True)
    )
    op.add_column(
        "investment_lots", sa.Column("discount_pct", sa.Numeric(5, 2), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("investment_lots", "discount_pct")
    op.drop_column("investment_lots", "fmv_at_acquisition")
