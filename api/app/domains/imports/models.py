"""Import column mapping model."""
from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from app.infra.db import Base


class ImportMapping(Base):
    """Saved CSV column mapping per institution."""
    __tablename__ = "import_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    institution: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    # JSON: {"date": "Date", "amount": "Montant", "description": "Libellé", ...}
    column_map: Mapped[dict] = mapped_column(JSONB, nullable=False)
    date_format: Mapped[str] = mapped_column(String(50), default="%d/%m/%Y")
    decimal_separator: Mapped[str] = mapped_column(String(1), default=",")
    encoding: Mapped[str] = mapped_column(String(20), default="utf-8")
    skip_rows: Mapped[int] = mapped_column(Integer, default=0)
