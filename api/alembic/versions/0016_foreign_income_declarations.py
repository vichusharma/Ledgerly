"""Add foreign_income_declarations table (Feature J2-S7, docs/Backlog.md)

Form 2047 foreign-source income lines — dividends, interest, salary,
capital gains, or other — one row per person per tax year per income
line. `elimination_method_override` lets a specific line diverge from
`TreatyMetadata`'s per-country default (Feature J4).

Revision ID: 0016
Revises: 0015
Create Date: 2026-07-07
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "foreign_income_declarations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("person_id", sa.Integer(), sa.ForeignKey("persons.id"), nullable=False),
        sa.Column("tax_year", sa.Integer(), nullable=False),
        sa.Column("income_type", sa.String(30), nullable=False),
        sa.Column("source_country_code", sa.String(2), nullable=False),
        sa.Column("source_description", sa.String(200), nullable=False),
        sa.Column("gross_amount_eur", sa.Numeric(14, 2), nullable=False),
        sa.Column(
            "foreign_tax_paid_eur", sa.Numeric(14, 2), nullable=False, server_default="0"
        ),
        sa.Column("elimination_method_override", sa.String(40), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("foreign_income_declarations")
