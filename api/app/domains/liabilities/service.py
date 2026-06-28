"""Liabilities service — loan CRUD, amortization, debt summary."""
from __future__ import annotations

import datetime
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.amortization import compute_schedule, interest_paid, remaining_capital
from app.domains.liabilities.models import AmortizationRow, Loan
from app.domains.liabilities.schemas import (
    AmortRowOut, DebtSummaryOut, LoanCreateIn, LoanOut, PrepaymentIn,
)


class LiabilityService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_loans(self) -> list[LoanOut]:
        result = await self.session.execute(select(Loan))
        return [LoanOut.model_validate(l) for l in result.scalars()]

    async def get_loan(self, loan_id: int) -> LoanOut | None:
        l = await self.session.get(Loan, loan_id)
        return LoanOut.model_validate(l) if l else None

    async def create_loan(self, body: LoanCreateIn) -> LoanOut:
        loan = Loan(**body.model_dump())
        self.session.add(loan)
        await self.session.flush()
        await self._regenerate_schedule(loan)
        return LoanOut.model_validate(loan)

    async def delete_loan(self, loan_id: int) -> None:
        await self.session.execute(
            delete(AmortizationRow).where(AmortizationRow.loan_id == loan_id)
        )
        loan = await self.session.get(Loan, loan_id)
        if loan:
            await self.session.delete(loan)

    async def get_schedule(self, loan_id: int) -> list[AmortRowOut] | None:
        loan = await self.session.get(Loan, loan_id)
        if loan is None:
            return None
        result = await self.session.execute(
            select(AmortizationRow)
            .where(AmortizationRow.loan_id == loan_id)
            .order_by(AmortizationRow.period)
        )
        return [AmortRowOut.model_validate(r) for r in result.scalars()]

    async def get_debt_summary(self, loan_id: int) -> DebtSummaryOut | None:
        loan = await self.session.get(Loan, loan_id)
        if loan is None:
            return None

        result = await self.session.execute(
            select(AmortizationRow)
            .where(AmortizationRow.loan_id == loan_id)
            .order_by(AmortizationRow.period)
        )
        db_rows = list(result.scalars())

        # Rebuild core rows for calculation
        core_rows = [
            type("R", (), {
                "period": r.period,
                "payment_date": r.payment_date,
                "payment": r.payment,
                "principal": r.principal,
                "interest": r.interest,
                "balance": r.balance,
            })()
            for r in db_rows
        ]

        today = datetime.date.today()
        start_of_year = today.replace(month=1, day=1)

        rem_cap = remaining_capital(core_rows, today)  # type: ignore[arg-type]
        interest_ytd = interest_paid(core_rows, start_of_year, today)  # type: ignore[arg-type]
        interest_total = interest_paid(core_rows)  # type: ignore[arg-type]

        future_rows = [r for r in db_rows if r.payment_date > today]
        next_row = future_rows[0] if future_rows else None

        return DebtSummaryOut(
            loan_id=loan_id,
            remaining_capital=rem_cap,
            interest_paid_ytd=interest_ytd,
            interest_paid_total=interest_total,
            total_payments_remaining=len(future_rows),
            next_payment_date=next_row.payment_date if next_row else None,
            next_payment_amount=next_row.payment if next_row else None,
        )

    async def apply_prepayment(self, loan_id: int, body: PrepaymentIn) -> LoanOut | None:
        """P2: apply a prepayment and recompute the schedule."""
        loan = await self.session.get(Loan, loan_id)
        if loan is None:
            return None
        loan.extra_principal_paid += body.amount
        await self._regenerate_schedule(loan)
        return LoanOut.model_validate(loan)

    async def _regenerate_schedule(self, loan: Loan) -> None:
        """Delete existing rows and recompute from core."""
        await self.session.execute(
            delete(AmortizationRow).where(AmortizationRow.loan_id == loan.id)
        )
        rows = compute_schedule(
            principal=loan.principal,
            annual_rate=loan.annual_rate,
            term_months=loan.term_months,
            start_date=loan.start_date,
            payment_day=loan.payment_day,
            extra_principal=loan.extra_principal_paid,
        )
        for row in rows:
            self.session.add(AmortizationRow(
                loan_id=loan.id,
                period=row.period,
                payment_date=row.payment_date,
                payment=row.payment,
                principal=row.principal,
                interest=row.interest,
                balance=row.balance,
            ))
        await self.session.flush()
