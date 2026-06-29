"""Reclassify regulated savings books (Livret A / LDDS / LEP) as savings

These products are cash savings accounts, but were created as
``investment_wrapper`` (the only type that exposed the product label).
That type computes net worth from investment lots + market prices, so their
imported transaction balances never reached the dashboard. ``savings`` sums
transactions directly, which is the correct behaviour for a Livret A.

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-29
"""
from __future__ import annotations

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE accounts
        SET type = 'savings'
        WHERE type = 'investment_wrapper'
          AND wrapper_type IN ('LIVRET_A', 'LDDS', 'LEP')
        """
    )


def downgrade() -> None:
    # Best-effort reversal: send the regulated savings books back to wrappers.
    op.execute(
        """
        UPDATE accounts
        SET type = 'investment_wrapper'
        WHERE type = 'savings'
          AND wrapper_type IN ('LIVRET_A', 'LDDS', 'LEP')
        """
    )
