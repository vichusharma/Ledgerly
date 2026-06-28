"""Initial schema — all tables.

Revision ID: 0001
Revises:
Create Date: 2026-06-28
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── households ──────────────────────────────────────────────────────────
    op.create_table(
        "households",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
    )

    # ── persons ─────────────────────────────────────────────────────────────
    op.create_table(
        "persons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("household_id", sa.Integer(), sa.ForeignKey("households.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default="false"),
    )

    # ── accounts ─────────────────────────────────────────────────────────────
    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("wrapper_type", sa.String(20), nullable=True),
        sa.Column("institution", sa.String(200), nullable=True),
        sa.Column("currency", sa.String(3), server_default="EUR"),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("persons.id"), nullable=False),
        sa.Column("joint_owner_id", sa.Integer(), sa.ForeignKey("persons.id"), nullable=True),
        sa.Column("ownership_pct", sa.Numeric(5, 2), server_default="100.00"),
        sa.Column("is_archived", sa.Boolean(), server_default="false"),
        sa.Column("notes", sa.Text(), nullable=True),
    )

    # ── categories ───────────────────────────────────────────────────────────
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("categories.id"), nullable=True),
        sa.Column("color", sa.String(7), nullable=True),
    )

    # ── category_rules ────────────────────────────────────────────────────────
    op.create_table(
        "category_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pattern", sa.String(500), nullable=False),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id"), nullable=False),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=True),
        sa.Column("priority", sa.Integer(), server_default="0"),
    )

    # ── import_mappings ───────────────────────────────────────────────────────
    op.create_table(
        "import_mappings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("institution", sa.String(200), nullable=False, unique=True),
        sa.Column("column_map", postgresql.JSONB(), nullable=False),
        sa.Column("date_format", sa.String(50), server_default="%d/%m/%Y"),
        sa.Column("decimal_separator", sa.String(1), server_default=","),
        sa.Column("encoding", sa.String(20), server_default="utf-8"),
        sa.Column("skip_rows", sa.Integer(), server_default="0"),
    )

    # ── import_batches ────────────────────────────────────────────────────────
    op.create_table(
        "import_batches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("imported_at", sa.DateTime(), nullable=False),
        sa.Column("row_count", sa.Integer(), server_default="0"),
        sa.Column("duplicate_count", sa.Integer(), server_default="0"),
        sa.Column("is_rolled_back", sa.Boolean(), server_default="false"),
    )

    # ── vacation_budgets (needed before transactions FK) ──────────────────────
    op.create_table(
        "vacation_budgets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("currency", sa.String(3), server_default="EUR"),
        sa.Column("planned_items", postgresql.JSONB(), server_default="[]"),
        sa.Column("notes", sa.Text(), nullable=True),
    )

    # ── recurring_expenses (needed before transactions FK) ────────────────────
    op.create_table(
        "recurring_expenses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("expected_amount", sa.Numeric(20, 4), nullable=False),
        sa.Column("currency", sa.String(3), server_default="EUR"),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id"), nullable=True),
        sa.Column("frequency", sa.String(20), server_default="monthly"),
        sa.Column("day_of_month", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
    )

    # ── transactions ──────────────────────────────────────────────────────────
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("import_batch_id", sa.Integer(), sa.ForeignKey("import_batches.id"), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(20, 4), nullable=False),
        sa.Column("currency", sa.String(3), server_default="EUR"),
        sa.Column("description", sa.String(500), server_default=""),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id"), nullable=True),
        sa.Column("dedup_hash", sa.String(64), nullable=False),
        sa.Column("is_split", sa.Boolean(), server_default="false"),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("transactions.id"), nullable=True),
        sa.Column("vacation_budget_id", sa.Integer(), sa.ForeignKey("vacation_budgets.id"), nullable=True),
        sa.Column("is_recurring", sa.Boolean(), server_default="false"),
        sa.Column("recurring_expense_id", sa.Integer(), sa.ForeignKey("recurring_expenses.id"), nullable=True),
        sa.UniqueConstraint("account_id", "dedup_hash", name="uq_txn_dedup"),
    )
    op.create_index("ix_transactions_account_date", "transactions", ["account_id", "date"])
    op.create_index("ix_transactions_category", "transactions", ["category_id"])

    # ── instruments ───────────────────────────────────────────────────────────
    op.create_table(
        "instruments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("isin", sa.String(12), nullable=True, unique=True),
        sa.Column("ticker", sa.String(20), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("asset_class", sa.String(20), server_default="equity"),
        sa.Column("region", sa.String(100), nullable=True),
        sa.Column("currency", sa.String(3), server_default="EUR"),
    )

    # ── vesting_schedules (before investment_lots FK) ─────────────────────────
    op.create_table(
        "vesting_schedules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("instrument_id", sa.Integer(), sa.ForeignKey("instruments.id"), nullable=False),
        sa.Column("grant_date", sa.Date(), nullable=False),
        sa.Column("total_shares", sa.Numeric(20, 8), nullable=False),
        sa.Column("cliff_months", sa.Integer(), server_default="12"),
        sa.Column("vesting_months", sa.Integer(), server_default="48"),
        sa.Column("grant_price", sa.Numeric(20, 6), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
    )

    # ── investment_lots ───────────────────────────────────────────────────────
    op.create_table(
        "investment_lots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("instrument_id", sa.Integer(), sa.ForeignKey("instruments.id"), nullable=True),
        sa.Column("lot_type", sa.String(20), nullable=False),
        sa.Column("quantity", sa.Numeric(20, 8), nullable=False),
        sa.Column("price", sa.Numeric(20, 6), nullable=False),
        sa.Column("fees", sa.Numeric(20, 4), server_default="0"),
        sa.Column("currency", sa.String(3), server_default="EUR"),
        sa.Column("settled_at", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("vesting_schedule_id", sa.Integer(), sa.ForeignKey("vesting_schedules.id"), nullable=True),
    )
    op.create_index("ix_lots_account_date", "investment_lots", ["account_id", "settled_at"])

    # ── instrument_prices ─────────────────────────────────────────────────────
    op.create_table(
        "instrument_prices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("instrument_id", sa.Integer(), sa.ForeignKey("instruments.id"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("close", sa.Numeric(20, 6), nullable=False),
        sa.Column("currency", sa.String(3), server_default="EUR"),
        sa.UniqueConstraint("instrument_id", "date", name="uq_price_instrument_date"),
    )
    op.create_index("ix_prices_instrument_date", "instrument_prices", ["instrument_id", "date"])

    # ── target_allocations ────────────────────────────────────────────────────
    op.create_table(
        "target_allocations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("asset_class", sa.String(50), nullable=False, unique=True),
        sa.Column("target_pct", sa.Numeric(5, 2), nullable=False),
    )

    # ── loans ─────────────────────────────────────────────────────────────────
    op.create_table(
        "loans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("type", sa.String(20), server_default="mortgage"),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("principal", sa.Numeric(20, 4), nullable=False),
        sa.Column("annual_rate", sa.Numeric(8, 6), nullable=False),
        sa.Column("term_months", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("payment_day", sa.Integer(), server_default="5"),
        sa.Column("currency", sa.String(3), server_default="EUR"),
        sa.Column("extra_principal_paid", sa.Numeric(20, 4), server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
    )

    # ── amortization_rows ─────────────────────────────────────────────────────
    op.create_table(
        "amortization_rows",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("loan_id", sa.Integer(), sa.ForeignKey("loans.id"), nullable=False),
        sa.Column("period", sa.Integer(), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("payment", sa.Numeric(20, 4), nullable=False),
        sa.Column("principal", sa.Numeric(20, 4), nullable=False),
        sa.Column("interest", sa.Numeric(20, 4), nullable=False),
        sa.Column("balance", sa.Numeric(20, 4), nullable=False),
    )

    # ── account_snapshots ─────────────────────────────────────────────────────
    op.create_table(
        "account_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("balance", sa.Numeric(20, 4), nullable=False),
        sa.Column("currency", sa.String(3), server_default="EUR"),
        sa.UniqueConstraint("account_id", "snapshot_date", name="uq_snapshot_account_date"),
    )
    op.create_index("ix_snapshots_date", "account_snapshots", ["snapshot_date"])

    # ── scenarios ─────────────────────────────────────────────────────────────
    op.create_table(
        "scenarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("type", sa.String(30), server_default="invest_vs_prepay"),
        sa.Column("parameters", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("last_result", postgresql.JSONB(), nullable=True),
        sa.Column("last_run_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # ── goals ─────────────────────────────────────────────────────────────────
    op.create_table(
        "goals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("type", sa.String(30), server_default="other"),
        sa.Column("target_amount", sa.Numeric(20, 4), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("currency", sa.String(3), server_default="EUR"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_achieved", sa.Boolean(), server_default="false"),
    )


def downgrade() -> None:
    for table in [
        "goals", "scenarios", "account_snapshots", "amortization_rows", "loans",
        "target_allocations", "instrument_prices", "investment_lots", "vesting_schedules",
        "instruments", "transactions", "recurring_expenses", "vacation_budgets",
        "import_batches", "import_mappings", "category_rules", "categories",
        "accounts", "persons", "households",
    ]:
        op.drop_table(table)
