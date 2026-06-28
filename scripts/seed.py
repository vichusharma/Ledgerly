#!/usr/bin/env python3
"""
Seed the Ledgerly database with realistic demo data for Antoine (primary persona).
Usage:  python scripts/seed.py
Env:    DATABASE_URL must be set (or .env loaded).
"""
import asyncio
import os
import sys
from datetime import date, timedelta
from decimal import Decimal

# Ensure api package is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

from app.infra.db import async_session_factory, init_db
from app.domains.accounts.models import Person, Account, AccountType
from app.domains.investments.models import Instrument, InvestmentLot, LotType, WrapperType
from app.domains.liabilities.models import Loan, LoanType
from app.domains.transactions.models import Category, Transaction


async def seed():
    await init_db()
    async with async_session_factory() as session:
        # --- Persons ---
        antoine = Person(name="Antoine", is_primary=True)
        camille = Person(name="Camille", is_primary=False)
        session.add_all([antoine, camille])
        await session.flush()

        # --- Accounts ---
        pea = Account(
            name="PEA Boursorama",
            type=AccountType.investment_wrapper,
            wrapper_type=WrapperType.PEA,
            institution="Boursorama",
            currency="EUR",
            owner_id=antoine.id,
            ownership_pct=Decimal("100.00"),
        )
        livret_a = Account(
            name="Livret A",
            type=AccountType.savings,
            wrapper_type=WrapperType.LIVRET_A,
            institution="La Banque Postale",
            currency="EUR",
            owner_id=antoine.id,
            ownership_pct=Decimal("100.00"),
        )
        joint_av = Account(
            name="AV Joint",
            type=AccountType.investment_wrapper,
            wrapper_type=WrapperType.AV,
            institution="Linxea",
            currency="EUR",
            owner_id=antoine.id,
            joint_owner_id=camille.id,
            ownership_pct=Decimal("50.00"),
        )
        checking = Account(
            name="Compte courant BNP",
            type=AccountType.bank,
            institution="BNP Paribas",
            currency="EUR",
            owner_id=antoine.id,
            ownership_pct=Decimal("100.00"),
        )
        session.add_all([pea, livret_a, joint_av, checking])
        await session.flush()

        # --- Instruments ---
        world_etf = Instrument(
            isin="IE00B4L5Y983",
            name="iShares Core MSCI World ETF",
            ticker="IWDA",
            asset_class="equity",
            region="global",
            currency="USD",
        )
        session.add(world_etf)
        await session.flush()

        # --- Lots ---
        lot1 = InvestmentLot(
            account_id=pea.id,
            instrument_id=world_etf.id,
            lot_type=LotType.buy,
            quantity=Decimal("10"),
            price=Decimal("70.00"),
            fees=Decimal("1.99"),
            currency="EUR",
            settled_at=date(2023, 3, 15),
        )
        lot2 = InvestmentLot(
            account_id=pea.id,
            instrument_id=world_etf.id,
            lot_type=LotType.buy,
            quantity=Decimal("5"),
            price=Decimal("78.00"),
            fees=Decimal("0.99"),
            currency="EUR",
            settled_at=date(2024, 1, 10),
        )
        session.add_all([lot1, lot2])

        # --- Mortgage ---
        mortgage = Loan(
            name="Crédit immobilier LCL",
            type=LoanType.mortgage,
            account_id=checking.id,
            principal=Decimal("280000.00"),
            annual_rate=Decimal("0.0185"),
            term_months=240,
            start_date=date(2021, 6, 1),
            payment_day=5,
            currency="EUR",
        )
        session.add(mortgage)

        # --- Categories ---
        utilities = Category(name="Utilities", parent_id=None)
        session.add(utilities)
        await session.flush()
        electricity = Category(name="Electricity", parent_id=utilities.id)
        internet = Category(name="Internet", parent_id=utilities.id)
        session.add_all([electricity, internet])

        await session.commit()
        print("✔ Demo data seeded successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
