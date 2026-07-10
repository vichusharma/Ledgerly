"""Add loans.manual_payment (Loan management + amortization simulation feature)

Optional override for the EMI/monthly payment — lets a user enter an
already-existing loan whose bank-quoted payment differs slightly from the
theoretical French annuite-constante formula (rounding, insurance riders).
When set, schedule generation treats term_months as advisory and iterates
until the balance reaches zero (capped by a safety iteration limit in
core/amortization.py, not persisted).

Revision ID: 0020
Revises: 0019
Create Date: 2026-07-10
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "loans", sa.Column("manual_payment", sa.Numeric(20, 4), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("loans", "manual_payment")
