"""Tax profile service — per-person impatriate settings, household filing
status + explicit dependents list. Feature I2 of docs/Backlog.md — facts
only, no tax computation yet (that's Feature I3)."""
from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.accounts.models import Person
from app.domains.accounts.repository import PersonRepository
from app.domains.tax.models import HouseholdTaxDependent, HouseholdTaxSettings
from app.domains.tax.schemas import (
    HouseholdTaxSettingsOut,
    HouseholdTaxSettingsUpdateIn,
    PersonTaxProfileOut,
    PersonTaxProfileUpdateIn,
)


class TaxService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._person_repo = PersonRepository(session)

    async def get_person_tax_profile(self, person_id: int) -> PersonTaxProfileOut | None:
        person = await self.session.get(Person, person_id)
        if person is None:
            return None
        return PersonTaxProfileOut(
            person_id=person.id,
            impatriate_enabled=person.impatriate_enabled,
            impatriate_arrival_date=person.impatriate_arrival_date,
            impatriate_election_method=person.impatriate_election_method,
        )

    async def set_person_tax_profile(
        self, person_id: int, body: PersonTaxProfileUpdateIn
    ) -> PersonTaxProfileOut | None:
        person = await self.session.get(Person, person_id)
        if person is None:
            return None
        person.impatriate_enabled = body.impatriate_enabled
        person.impatriate_arrival_date = body.impatriate_arrival_date
        person.impatriate_election_method = body.impatriate_election_method
        await self.session.flush()
        return await self.get_person_tax_profile(person_id)

    async def _get_or_create_settings(self) -> HouseholdTaxSettings:
        household = await self._person_repo.get_household()
        if household is None:
            raise ValueError("No household configured. Call /auth/setup first.")
        result = await self.session.execute(
            select(HouseholdTaxSettings).where(
                HouseholdTaxSettings.household_id == household.id
            )
        )
        settings = result.scalar_one_or_none()
        if settings is None:
            settings = HouseholdTaxSettings(household_id=household.id)
            self.session.add(settings)
            await self.session.flush()
        return settings

    async def get_household_tax_settings(self) -> HouseholdTaxSettingsOut:
        settings = await self._get_or_create_settings()
        dependents = await self.session.execute(
            select(HouseholdTaxDependent.person_id).where(
                HouseholdTaxDependent.household_tax_settings_id == settings.id
            )
        )
        return HouseholdTaxSettingsOut(
            filing_status=settings.filing_status,
            dependent_person_ids=sorted(row[0] for row in dependents),
        )

    async def set_household_tax_settings(
        self, body: HouseholdTaxSettingsUpdateIn
    ) -> HouseholdTaxSettingsOut:
        persons = await self._person_repo.list_persons()
        valid_ids = {p.id for p in persons}
        unknown = [pid for pid in body.dependent_person_ids if pid not in valid_ids]
        if unknown:
            raise ValueError(f"Unknown person_id(s) for dependents: {unknown}")

        settings = await self._get_or_create_settings()
        settings.filing_status = body.filing_status
        await self.session.execute(
            delete(HouseholdTaxDependent).where(
                HouseholdTaxDependent.household_tax_settings_id == settings.id
            )
        )
        for person_id in set(body.dependent_person_ids):
            self.session.add(
                HouseholdTaxDependent(
                    household_tax_settings_id=settings.id, person_id=person_id
                )
            )
        await self.session.flush()
        return await self.get_household_tax_settings()
