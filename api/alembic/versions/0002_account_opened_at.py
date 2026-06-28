"""Add opened_at and created_at to accounts

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-28
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "accounts",
        sa.Column("opened_at", sa.Date(), nullable=True),
    )
    op.add_column(
        "accounts",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("accounts", "created_at")
    op.drop_column("accounts", "opened_at")
