"""Add treaty_metadata table, seeded with a handful of countries

Reference data for double-taxation-treaty elimination methods, seeded
for a handful of plausible expat-origin countries only — NOT all ~120
French tax treaties. Any country not seeded here falls back at compute
time (Feature J4) to the credit method ("credit_equal_to_french_tax")
with a disclosed `treaty_method_defaulted_unseeded_country`
simplification flag. See Feature J1 in docs/Backlog.md.

Revision ID: 0013
Revises: 0012
Create Date: 2026-07-07
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None

SEEDED_TREATIES = [
    {
        "country_code": "IN",
        "country_name": "India",
        "default_elimination_method": "credit_equal_to_french_tax",
        "treaty_reference": "Convention France-Inde du 29/09/1992",
        "notes": None,
    },
    {
        "country_code": "US",
        "country_name": "United States",
        "default_elimination_method": "credit_equal_to_french_tax",
        "treaty_reference": "Convention France-Etats-Unis du 31/08/1994",
        "notes": None,
    },
    {
        "country_code": "GB",
        "country_name": "United Kingdom",
        "default_elimination_method": "credit_equal_to_french_tax",
        "treaty_reference": "Convention France-Royaume-Uni du 19/06/2008",
        "notes": None,
    },
    {
        "country_code": "CA",
        "country_name": "Canada",
        "default_elimination_method": "credit_equal_to_french_tax",
        "treaty_reference": "Convention France-Canada du 02/05/1975",
        "notes": None,
    },
    {
        "country_code": "DE",
        "country_name": "Germany",
        "default_elimination_method": "exemption_with_effective_rate",
        "treaty_reference": "Convention France-Allemagne du 21/07/1959",
        "notes": None,
    },
]


def upgrade() -> None:
    op.create_table(
        "treaty_metadata",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("country_code", sa.String(2), nullable=False),
        sa.Column("country_name", sa.String(100), nullable=False),
        sa.Column("default_elimination_method", sa.String(40), nullable=False),
        sa.Column("treaty_reference", sa.String(200), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_unique_constraint(
        "uq_treaty_metadata_country_code", "treaty_metadata", ["country_code"]
    )

    treaty_metadata = sa.table(
        "treaty_metadata",
        sa.column("country_code", sa.String(2)),
        sa.column("country_name", sa.String(100)),
        sa.column("default_elimination_method", sa.String(40)),
        sa.column("treaty_reference", sa.String(200)),
        sa.column("notes", sa.Text()),
    )
    op.bulk_insert(treaty_metadata, SEEDED_TREATIES)


def downgrade() -> None:
    op.drop_table("treaty_metadata")
