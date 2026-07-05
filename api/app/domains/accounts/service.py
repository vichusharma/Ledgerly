"""Accounts service — business logic."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.accounts.repository import AccountRepository, PersonRepository
from app.domains.accounts.schemas import (
    AccountCreateIn, AccountOut, AccountUpdateIn,
    HouseholdSettingsOut, HouseholdSettingsUpdateIn, PersonCreateIn, PersonOut,
)


class AccountService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._person_repo = PersonRepository(session)
        self._account_repo = AccountRepository(session)

    async def list_persons(self) -> list[PersonOut]:
        persons = await self._person_repo.list_persons()
        return [PersonOut.model_validate(p) for p in persons]

    async def create_person(self, body: PersonCreateIn) -> PersonOut:
        household = await self._person_repo.get_household()
        if household is None:
            raise ValueError("No household configured. Call /auth/setup first.")
        person = await self._person_repo.create_person(
            name=body.name,
            is_primary=body.is_primary,
            household_id=household.id,
        )
        return PersonOut.model_validate(person)

    async def list_accounts(
        self, scope: str = "household", include_archived: bool = False
    ) -> list[AccountOut]:
        # Scope: "household" = all persons, else filter by person_id
        persons = await self._person_repo.list_persons()
        if scope == "household":
            person_ids = [p.id for p in persons]
        else:
            try:
                person_ids = [int(scope)]
            except ValueError:
                person_ids = [p.id for p in persons]

        accounts = await self._account_repo.list_accounts(
            person_ids=person_ids, include_archived=include_archived
        )
        return [AccountOut.model_validate(a) for a in accounts]

    async def get_account(self, account_id: int) -> AccountOut | None:
        a = await self._account_repo.get_account(account_id)
        return AccountOut.model_validate(a) if a else None

    async def create_account(self, body: AccountCreateIn) -> AccountOut:
        a = await self._account_repo.create_account(
            name=body.name,
            type=body.type,
            wrapper_type=body.wrapper_type,
            institution=body.institution,
            currency=body.currency,
            owner_id=body.owner_id,
            joint_owner_id=body.joint_owner_id,
            ownership_pct=body.ownership_pct,
            notes=body.notes,
        )
        return AccountOut.model_validate(a)

    async def update_account(self, account_id: int, body: AccountUpdateIn) -> AccountOut | None:
        a = await self._account_repo.get_account(account_id)
        if a is None:
            return None
        updates = body.model_dump(exclude_unset=True)
        a = await self._account_repo.update_account(a, **updates)
        return AccountOut.model_validate(a)

    async def archive_account(self, account_id: int) -> None:
        await self._account_repo.archive_account(account_id)

    async def get_household_settings(self) -> HouseholdSettingsOut:
        household = await self._person_repo.get_household()
        if household is None:
            raise ValueError("No household configured. Call /auth/setup first.")
        return HouseholdSettingsOut(price_lookup_enabled=household.price_lookup_enabled)

    async def update_household_settings(
        self, body: HouseholdSettingsUpdateIn
    ) -> HouseholdSettingsOut:
        household = await self._person_repo.update_price_lookup(body.price_lookup_enabled)
        return HouseholdSettingsOut(price_lookup_enabled=household.price_lookup_enabled)
