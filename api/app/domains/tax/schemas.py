"""Tax domain schemas."""
from __future__ import annotations

import datetime

from pydantic import BaseModel

from app.domains.accounts.models import ImpatriateElectionMethod
from app.domains.tax.models import FilingStatus


class PersonTaxProfileOut(BaseModel):
    person_id: int
    impatriate_enabled: bool
    impatriate_arrival_date: datetime.date | None
    impatriate_election_method: ImpatriateElectionMethod | None


class PersonTaxProfileUpdateIn(BaseModel):
    impatriate_enabled: bool
    impatriate_arrival_date: datetime.date | None = None
    impatriate_election_method: ImpatriateElectionMethod | None = None


class HouseholdTaxSettingsOut(BaseModel):
    filing_status: FilingStatus
    dependent_person_ids: list[int]


class HouseholdTaxSettingsUpdateIn(BaseModel):
    filing_status: FilingStatus
    dependent_person_ids: list[int] = []
