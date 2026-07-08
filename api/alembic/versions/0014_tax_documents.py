"""Add tax_documents table (encrypted source-document audit trail)

Feature J3 (docs/Backlog.md), pulled forward ahead of Feature J2 in
the delivery order since J2's parser-confirm flows depend on this
table existing to persist the reviewed source PDF. Stores
Fernet-encrypted bytes (see `app/infra/document_crypto.py`) keyed from
the existing, previously-unused `Settings.encryption_key`.

Revision ID: 0014
Revises: 0013
Create Date: 2026-07-07
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tax_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("person_id", sa.Integer(), sa.ForeignKey("persons.id"), nullable=True),
        sa.Column("tax_year", sa.Integer(), nullable=True),
        sa.Column("document_type", sa.String(30), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("encrypted_content", sa.LargeBinary(), nullable=False),
        sa.Column("related_record_type", sa.String(50), nullable=True),
        sa.Column("related_record_id", sa.Integer(), nullable=True),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("tax_documents")
