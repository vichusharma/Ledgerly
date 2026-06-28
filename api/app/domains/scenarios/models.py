"""Scenarios domain models."""
from __future__ import annotations

import datetime
import enum
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.db import Base


class ScenarioType(str, enum.Enum):
    invest_vs_prepay = "invest_vs_prepay"
    goal_feasibility = "goal_feasibility"
    monte_carlo = "monte_carlo"


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[ScenarioType] = mapped_column(
        String(50), default=ScenarioType.invest_vs_prepay
    )
    # Parameters stored as JSON so we can add new scenario types without migrations
    parameters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # Latest result (cached)
    last_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    last_run_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
