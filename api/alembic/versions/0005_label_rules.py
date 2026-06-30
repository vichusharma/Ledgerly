"""Add label_rules table.

Label rules map a regex pattern to a label so that labels can be
auto-applied to transactions at import time, mirroring category_rules.
Unlike categories (single-valued), labels are cumulative: a description
may match several rules and receive several labels.

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-30
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "label_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pattern", sa.String(500), nullable=False),
        sa.Column(
            "label_id",
            sa.Integer(),
            sa.ForeignKey("labels.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("label_rules")
