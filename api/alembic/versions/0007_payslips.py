"""Add payslips table

Stores reviewed/confirmed French payslip ("bulletin de paie") data per
person per pay period, upserted by the (person_id, pay_period) natural
key. Deliberately siloed from the Transactions ledger — see Feature I1
in docs/Backlog.md.

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-06
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payslips",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("person_id", sa.Integer(), sa.ForeignKey("persons.id"), nullable=False),
        sa.Column("pay_period", sa.Date(), nullable=False),
        sa.Column("employer", sa.String(200), nullable=True),
        sa.Column("gross", sa.Numeric(12, 2), nullable=True),
        sa.Column("net_taxable", sa.Numeric(12, 2), nullable=True),
        sa.Column("net_before_tax", sa.Numeric(12, 2), nullable=True),
        sa.Column("net_paid", sa.Numeric(12, 2), nullable=True),
        sa.Column("pas_rate", sa.Numeric(5, 2), nullable=True),
        sa.Column("pas_withheld", sa.Numeric(12, 2), nullable=True),
        sa.Column("ytd_gross", sa.Numeric(12, 2), nullable=True),
        sa.Column("ytd_net_taxable", sa.Numeric(12, 2), nullable=True),
        sa.Column("ytd_pas_withheld", sa.Numeric(12, 2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
    )
    op.create_unique_constraint(
        "uq_payslip_person_period", "payslips", ["person_id", "pay_period"]
    )


def downgrade() -> None:
    op.drop_table("payslips")
