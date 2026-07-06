"""Add household_tax_settings + household_tax_dependents tables

Household-wide filing status and an explicit, opt-in dependents list
(never auto-inferred from age/relationship) — see Feature I2 in
docs/Backlog.md.

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-06
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "household_tax_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "household_id", sa.Integer(), sa.ForeignKey("households.id"), nullable=False
        ),
        sa.Column(
            "filing_status", sa.String(20), nullable=False, server_default="single"
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_unique_constraint(
        "uq_household_tax_settings_household", "household_tax_settings", ["household_id"]
    )

    op.create_table(
        "household_tax_dependents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "household_tax_settings_id",
            sa.Integer(),
            sa.ForeignKey("household_tax_settings.id"),
            nullable=False,
        ),
        sa.Column("person_id", sa.Integer(), sa.ForeignKey("persons.id"), nullable=False),
    )
    op.create_unique_constraint(
        "uq_tax_dependent_settings_person",
        "household_tax_dependents",
        ["household_tax_settings_id", "person_id"],
    )


def downgrade() -> None:
    op.drop_table("household_tax_dependents")
    op.drop_table("household_tax_settings")
