"""Accounts repository — DB queries."""
from __future__ import annotations

import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.accounts.models import Account, Household, Person


class PersonRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_household(self) -> Household | None:
        result = await self.session.execute(select(Household).limit(1))
        return result.scalar_one_or_none()

    async def create_household(self, password_hash: str) -> Household:
        household = Household(password_hash=password_hash)
        self.session.add(household)
        await self.session.flush()
        return household

    async def update_price_lookup(self, enabled: bool) -> Household:
        household = await self.get_household()
        if household is None:
            raise ValueError("No household configured.")
        household.price_lookup_enabled = enabled
        await self.session.flush()
        return household

    async def list_persons(self) -> list[Person]:
        result = await self.session.execute(select(Person))
        return list(result.scalars().all())

    async def get_person(self, person_id: int) -> Person | None:
        return await self.session.get(Person, person_id)

    async def create_person(
        self,
        name: str,
        is_primary: bool,
        household_id: int,
        date_of_birth: datetime.date | None = None,
    ) -> Person:
        person = Person(
            name=name, is_primary=is_primary, household_id=household_id,
            date_of_birth=date_of_birth,
        )
        self.session.add(person)
        await self.session.flush()
        return person

    async def update_person(self, person: Person, **kwargs: object) -> Person:
        for k, v in kwargs.items():
            setattr(person, k, v)
        await self.session.flush()
        return person


class AccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_accounts(
        self,
        person_ids: list[int] | None = None,
        include_archived: bool = False,
    ) -> list[Account]:
        stmt = select(Account)
        if not include_archived:
            stmt = stmt.where(Account.is_archived.is_(False))
        if person_ids:
            stmt = stmt.where(
                (Account.owner_id.in_(person_ids)) |
                (Account.joint_owner_id.in_(person_ids))
            )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_account(self, account_id: int) -> Account | None:
        return await self.session.get(Account, account_id)

    async def create_account(self, **kwargs: object) -> Account:
        account = Account(**kwargs)
        self.session.add(account)
        await self.session.flush()
        return account

    async def update_account(self, account: Account, **kwargs: object) -> Account:
        for k, v in kwargs.items():
            setattr(account, k, v)
        await self.session.flush()
        return account

    async def archive_account(self, account_id: int) -> None:
        account = await self.get_account(account_id)
        if account:
            account.is_archived = True
            await self.session.flush()
