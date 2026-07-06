"""Add per-person impatriate tax-regime columns

Adds the French expat "régime des impatriés" (Art. 155 B CGI) toggle to
Person, generically — any person can independently enable/disable it,
with their own arrival date and election method. See Feature I2 in
docs/Backlog.md.

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-06
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "persons",
        sa.Column(
            "impatriate_enabled", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.add_column(
        "persons", sa.Column("impatriate_arrival_date", sa.Date(), nullable=True)
    )
    op.add_column(
        "persons", sa.Column("impatriate_election_method", sa.String(20), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("persons", "impatriate_election_method")
    op.drop_column("persons", "impatriate_arrival_date")
    op.drop_column("persons", "impatriate_enabled")
