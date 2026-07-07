"""Add tax_year_configs table, seeded with a placeholder 2026 barème

The barème progressif changes yearly via Loi de Finances; this table
makes updating it a data migration rather than a code change (Feature
I3, docs/Backlog.md).

IMPORTANT — the seeded 2026 row uses the last officially published
brackets (2025 Loi de Finances, applicable to 2024 income) as a
placeholder/estimate: no 2026 barème has been officially legislated at
the time of writing. Replace this row (via a new migration, once
confirmed) with the real 2026 figures when the Loi de Finances is
published. Surfaced to the user as a disclaimer, not applied silently.

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-06
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None

# Placeholder — last known official brackets (2025 LF, 2024 income), used
# as a stand-in for 2026 pending an official publication.
PLACEHOLDER_2026_BRACKETS = [
    {"up_to": 11497, "rate": 0.0},
    {"up_to": 29315, "rate": 0.11},
    {"up_to": 83823, "rate": 0.30},
    {"up_to": 180294, "rate": 0.41},
    {"up_to": None, "rate": 0.45},
]
PLACEHOLDER_PLAFOND_PER_HALF_PART = 1791.00


def upgrade() -> None:
    op.create_table(
        "tax_year_configs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tax_year", sa.Integer(), nullable=False),
        sa.Column("brackets", JSONB(), nullable=False),
        sa.Column(
            "quotient_familial_plafond_per_half_part", sa.Numeric(10, 2), nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
    )
    op.create_unique_constraint(
        "uq_tax_year_configs_tax_year", "tax_year_configs", ["tax_year"]
    )

    tax_year_configs = sa.table(
        "tax_year_configs",
        sa.column("tax_year", sa.Integer()),
        sa.column("brackets", JSONB()),
        sa.column("quotient_familial_plafond_per_half_part", sa.Numeric(10, 2)),
    )
    op.bulk_insert(
        tax_year_configs,
        [
            {
                "tax_year": 2026,
                "brackets": PLACEHOLDER_2026_BRACKETS,
                "quotient_familial_plafond_per_half_part": PLACEHOLDER_PLAFOND_PER_HALF_PART,
            }
        ],
    )


def downgrade() -> None:
    op.drop_table("tax_year_configs")
