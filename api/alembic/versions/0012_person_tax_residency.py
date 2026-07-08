"""Add person_tax_residency table

Per-person tax-residency facts (home country, foreign/French tax IDs) —
the first table of Epic J's French Expat Tax Filing Module. Kept on its
own table rather than more `Person` columns since it's cohesive to the
filing domain, not a universal identity fact — see Feature J1 in
docs/Backlog.md.

Revision ID: 0012
Revises: 0011
Create Date: 2026-07-07
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "person_tax_residency",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "person_id", sa.Integer(), sa.ForeignKey("persons.id"), nullable=False
        ),
        sa.Column("home_country_code", sa.String(2), nullable=True),
        sa.Column("home_country_tax_id", sa.String(100), nullable=True),
        sa.Column("french_tax_number", sa.String(50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_unique_constraint(
        "uq_person_tax_residency_person", "person_tax_residency", ["person_id"]
    )


def downgrade() -> None:
    op.drop_table("person_tax_residency")
