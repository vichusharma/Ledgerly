"""Add labels + transaction_labels association table.

Labels are free-form user tags that can be applied to any number of
transactions (many-to-many).  They are distinct from categories, which
are auto-assigned and mutually exclusive; labels are cumulative and
user-driven (e.g. 'vacation', 'reimbursable', 'shared').

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-29
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "labels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("color", sa.String(7), nullable=False, server_default="#94a3b8"),
    )
    op.create_unique_constraint("uq_label_name", "labels", ["name"])

    op.create_table(
        "transaction_labels",
        sa.Column(
            "transaction_id",
            sa.Integer(),
            sa.ForeignKey("transactions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "label_id",
            sa.Integer(),
            sa.ForeignKey("labels.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("transaction_labels")
    op.drop_table("labels")
