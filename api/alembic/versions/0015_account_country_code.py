"""Add accounts.country_code (Feature J2-S6, docs/Backlog.md)

Persistent per-account fact — null means France (the app's implicit
default for every existing account) — needed for Form 3916 foreign
bank account declarations. Same "extend the existing table with a
persistent fact" precedent as `opened_at` (Feature I4).

Revision ID: 0015
Revises: 0014
Create Date: 2026-07-07
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("accounts", sa.Column("country_code", sa.String(2), nullable=True))


def downgrade() -> None:
    op.drop_column("accounts", "country_code")
