"""Add persons.date_of_birth

A generic per-person fact (not tax-specific) — needed so the quotient
familial engine can tell whether a dependent is a minor child (counted
via the standard progressive 0.5/1-by-position rule) or an adult
dependent (each a flat 1 full part), per Feature I2.1 of
docs/Backlog.md.

Revision ID: 0011
Revises: 0010
Create Date: 2026-07-07
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("persons", sa.Column("date_of_birth", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("persons", "date_of_birth")
