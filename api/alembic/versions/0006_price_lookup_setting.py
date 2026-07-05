"""Add price_lookup_enabled to households

Household-level opt-in flag gating the external (Yahoo Finance) price
provider — default off, matching the "100% local" promise until the
user explicitly enables it in Settings.

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-05
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "households",
        sa.Column(
            "price_lookup_enabled",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("households", "price_lookup_enabled")
