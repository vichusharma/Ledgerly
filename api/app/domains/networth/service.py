"""Net worth service — snapshots + time series."""
from __future__ import annotations

import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.accounts.models import Account, AccountType, Person
from app.domains.investments.models import Instrument, InstrumentPrice, InvestmentLot, LotType
from app.domains.liabilities.models import AmortizationRow, Loan
from app.domains.networth.models import AccountSnapshot
from app.domains.transactions.models import Transaction
from app.domains.networth.schemas import NetWorthBreakdown, NetWorthOut, NetWorthSeriesOut


class NetWorthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def take_snapshot(self) -> None:
        """Freeze today's account balances into AccountSnapshot rows."""
        today = datetime.date.today()
        accounts_result = await self.session.execute(
            select(Account).where(Account.is_archived.is_(False))
        )
        accounts = list(accounts_result.scalars())

        for account in accounts:
            balance = await self._compute_account_balance(account, today)
            # Upsert snapshot
            existing = await self.session.execute(
                select(AccountSnapshot).where(
                    AccountSnapshot.account_id == account.id,
                    AccountSnapshot.snapshot_date == today,
                )
            )
            snap = existing.scalar_one_or_none()
            if snap:
                snap.balance = balance
            else:
                self.session.add(AccountSnapshot(
                    account_id=account.id,
                    snapshot_date=today,
                    balance=balance,
                    currency=account.currency,
                ))
        await self.session.flush()

    async def get_networth(
        self,
        scope: str = "household",
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> NetWorthOut:
        today = datetime.date.today()
        accounts_result = await self.session.execute(
            select(Account).where(Account.is_archived.is_(False))
        )
        accounts = list(accounts_result.scalars())

        total_assets = Decimal("0")
        total_liabilities = Decimal("0")
        by_person: dict[str, NetWorthBreakdown] = {}

        for account in accounts:
            balance = await self._compute_account_balance(account, today)
            effective_balance = balance * (account.ownership_pct / Decimal("100"))

            if account.type == AccountType.liability:
                total_liabilities += effective_balance
            else:
                total_assets += effective_balance

            # Per-person breakdown
            persons_result = await self.session.execute(
                select(Person).where(Person.id == account.owner_id)
            )
            owner = persons_result.scalar_one_or_none()
            if owner:
                key = owner.name
                if key not in by_person:
                    by_person[key] = NetWorthBreakdown(
                        assets=Decimal("0"), liabilities=Decimal("0"), net_worth=Decimal("0")
                    )
                if account.type == AccountType.liability:
                    by_person[key] = NetWorthBreakdown(
                        assets=by_person[key].assets,
                        liabilities=by_person[key].liabilities + effective_balance,
                        net_worth=by_person[key].net_worth - effective_balance,
                    )
                else:
                    by_person[key] = NetWorthBreakdown(
                        assets=by_person[key].assets + effective_balance,
                        liabilities=by_person[key].liabilities,
                        net_worth=by_person[key].net_worth + effective_balance,
                    )

        net_worth = total_assets - total_liabilities
        return NetWorthOut(
            current=net_worth,
            assets=total_assets,
            liabilities=total_liabilities,
            by_person=by_person,
        )

    async def get_series(
        self,
        scope: str = "household",
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> list[NetWorthSeriesOut]:
        """Return net-worth time series from account snapshots."""
        stmt = select(AccountSnapshot.snapshot_date).distinct().order_by(
            AccountSnapshot.snapshot_date
        )
        if from_date:
            stmt = stmt.where(
                AccountSnapshot.snapshot_date >= datetime.date.fromisoformat(from_date)
            )
        if to_date:
            stmt = stmt.where(
                AccountSnapshot.snapshot_date <= datetime.date.fromisoformat(to_date)
            )
        dates_result = await self.session.execute(stmt)
        dates = list(dates_result.scalars())

        series: list[NetWorthSeriesOut] = []
        for snap_date in dates:
            snaps_result = await self.session.execute(
                select(AccountSnapshot).where(AccountSnapshot.snapshot_date == snap_date)
            )
            snaps = list(snaps_result.scalars())

            assets = Decimal("0")
            liabilities = Decimal("0")
            for snap in snaps:
                account = await self.session.get(Account, snap.account_id)
                if account is None or account.is_archived:
                    continue
                eff = snap.balance * (account.ownership_pct / Decimal("100"))
                if account.type == AccountType.liability:
                    liabilities += eff
                else:
                    assets += eff

            series.append(NetWorthSeriesOut(
                date=snap_date,
                net_worth=assets - liabilities,
                assets=assets,
                liabilities=liabilities,
            ))

        return series

    async def _compute_account_balance(
        self, account: Account, as_of: datetime.date
    ) -> Decimal:
        """Compute the current balance for any account type."""
        if account.type in (AccountType.bank, AccountType.savings):
            # Sum all non-split-parent transactions up to as_of to get running balance
            result = await self.session.execute(
                select(func.sum(Transaction.amount)).where(
                    Transaction.account_id == account.id,
                    Transaction.date <= as_of,
                    Transaction.is_split.is_(False),
                )
            )
            total = result.scalar_one_or_none()
            return total if total is not None else Decimal("0")

        elif account.type == AccountType.investment_wrapper:
            # Per instrument: the latest statement valuation lot (≤ as_of) is the
            # authoritative value; only instruments without one fall back to the
            # buy-lot × latest-price computation. Valuation lots are never summed
            # with each other or with buy lots for the same instrument.
            lots_result = await self.session.execute(
                select(InvestmentLot).where(
                    InvestmentLot.account_id == account.id,
                    InvestmentLot.lot_type.in_([LotType.buy, LotType.valuation]),
                    InvestmentLot.settled_at <= as_of,
                )
            )
            lots = list(lots_result.scalars())

            valuations: dict[int, InvestmentLot] = {}
            for lot in lots:
                if lot.lot_type == LotType.valuation and lot.instrument_id:
                    cur = valuations.get(lot.instrument_id)
                    if cur is None or (lot.settled_at, lot.id) > (cur.settled_at, cur.id):
                        valuations[lot.instrument_id] = lot

            total = Decimal("0")
            for v in valuations.values():
                total += v.quantity * v.price

            for lot in lots:
                if lot.lot_type != LotType.buy:
                    continue
                if lot.instrument_id:
                    if lot.instrument_id in valuations:
                        continue  # statement value supersedes computed value
                    price_result = await self.session.execute(
                        select(InstrumentPrice)
                        .where(
                            InstrumentPrice.instrument_id == lot.instrument_id,
                            InstrumentPrice.date <= as_of,
                        )
                        .order_by(InstrumentPrice.date.desc())
                        .limit(1)
                    )
                    price = price_result.scalar_one_or_none()
                    if price:
                        total += lot.quantity * price.close
                else:
                    total += lot.quantity * lot.price
            return total

        elif account.type == AccountType.liability:
            # Use remaining capital from amortization schedule
            loans_result = await self.session.execute(
                select(Loan).where(Loan.account_id == account.id)
            )
            loan = loans_result.scalar_one_or_none()
            if loan is None:
                return Decimal("0")
            rows_result = await self.session.execute(
                select(AmortizationRow)
                .where(
                    AmortizationRow.loan_id == loan.id,
                    AmortizationRow.payment_date <= as_of,
                )
                .order_by(AmortizationRow.period.desc())
                .limit(1)
            )
            last_row = rows_result.scalar_one_or_none()
            return last_row.balance if last_row else loan.principal

        return Decimal("0")
