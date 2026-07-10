"""Liabilities service — loan CRUD, amortization, debt summary."""
from __future__ import annotations

import datetime
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.amortization import (
    AmortRow, compute_schedule, interest_paid, recompute_from_midpoint, remaining_capital,
)
from app.domains.liabilities.models import AmortizationRow, Loan
from app.domains.liabilities.schemas import (
    AmortRowOut, DebtSummaryOut, LoanCreateIn, LoanOut, LoanUpdateIn,
    PrepaymentIn, PrepaymentPreviewOut, PrepaymentScenarioOut,
)

# Wire-level reduction_mode ("term"/"payment", kept for API back-compat) mapped to
# the core engine's mode names.
_MODE_MAP = {"term": "reduce_term", "payment": "reduce_emi"}


class LiabilityService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_loans(self) -> list[LoanOut]:
        from app.domains.accounts.models import Account

        result = await self.session.execute(select(Loan))
        loans = list(result.scalars())
        account_ids = [l.account_id for l in loans]
        institutions: dict[int, str | None] = {}
        if account_ids:
            accounts_result = await self.session.execute(
                select(Account.id, Account.institution).where(Account.id.in_(account_ids))
            )
            institutions = dict(accounts_result.all())

        outs = []
        for l in loans:
            out = LoanOut.model_validate(l)
            out.institution = institutions.get(l.account_id)
            outs.append(out)
        return outs

    async def get_loan(self, loan_id: int) -> LoanOut | None:
        from app.domains.accounts.models import Account

        l = await self.session.get(Loan, loan_id)
        if l is None:
            return None
        account = await self.session.get(Account, l.account_id)
        out = LoanOut.model_validate(l)
        out.institution = account.institution if account else None
        return out

    async def create_loan(self, body: LoanCreateIn) -> LoanOut:
        from app.domains.accounts.models import AccountType
        from app.domains.accounts.schemas import AccountCreateIn
        from app.domains.accounts.service import AccountService

        account = await AccountService(self.session).create_account(AccountCreateIn(
            name=body.name,
            type=AccountType.liability,
            institution=body.institution,
            currency=body.currency,
            owner_id=body.owner_id,
            joint_owner_id=body.joint_owner_id,
            ownership_pct=body.ownership_pct,
            opened_at=body.start_date,
        ))

        loan_fields = body.model_dump(
            exclude={"owner_id", "joint_owner_id", "ownership_pct", "institution"}
        )
        loan = Loan(**loan_fields, account_id=account.id)
        self.session.add(loan)
        await self.session.flush()
        await self._regenerate_schedule(loan)
        out = LoanOut.model_validate(loan)
        out.institution = account.institution
        return out

    async def update_loan(self, loan_id: int, body: LoanUpdateIn) -> LoanOut | None:
        """`name` and `institution` are also mirrored onto the linked Account
        (institution lives there exclusively, and the two names would otherwise
        silently drift apart across `/accounts` and `/debt`)."""
        loan = await self.session.get(Loan, loan_id)
        if loan is None:
            return None
        from app.domains.accounts.schemas import AccountUpdateIn
        from app.domains.accounts.service import AccountService

        updates = body.model_dump(exclude_unset=True)
        institution = updates.pop("institution", None)
        account_updates = {k: v for k, v in updates.items() if k == "name"}
        if institution is not None:
            account_updates["institution"] = institution
        for k, v in updates.items():
            setattr(loan, k, v)

        account_service = AccountService(self.session)
        account_out = (
            await account_service.update_account(loan.account_id, AccountUpdateIn(**account_updates))
            if account_updates
            else await account_service.get_account(loan.account_id)
        )
        await self.session.flush()
        out = LoanOut.model_validate(loan)
        out.institution = account_out.institution if account_out else None
        return out

    async def delete_loan(self, loan_id: int) -> None:
        loan = await self.session.get(Loan, loan_id)
        if loan is None:
            return
        account_id = loan.account_id
        await self.session.execute(
            delete(AmortizationRow).where(AmortizationRow.loan_id == loan_id)
        )
        await self.session.delete(loan)
        await self.session.flush()

        from app.domains.accounts.service import AccountService
        await AccountService(self.session).archive_account(account_id)

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

        db_rows = await self._get_rows(loan_id)
        core_rows = self._to_core_rows(db_rows)

        today = datetime.date.today()
        start_of_year = today.replace(month=1, day=1)

        rem_cap = remaining_capital(core_rows, today)
        interest_ytd = interest_paid(core_rows, start_of_year, today)
        interest_total = interest_paid(core_rows)

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

    async def preview_prepayment(
        self, loan_id: int, body: PrepaymentIn
    ) -> PrepaymentPreviewOut | None:
        """Non-destructive: computes both reduce_term and reduce_emi scenarios
        without writing anything to the database."""
        loan = await self.session.get(Loan, loan_id)
        if loan is None:
            return None

        applied_date, future_before, outstanding_balance, resume_period, resume_anchor, \
            current_payment = await self._prepayment_context(loan, applied_date=body.applied_date)
        baseline_interest = sum((r.interest for r in future_before), Decimal("0"))

        scenarios: dict[str, PrepaymentScenarioOut] = {}
        for core_mode in ("reduce_term", "reduce_emi"):
            new_rows = recompute_from_midpoint(
                outstanding_balance=outstanding_balance,
                annual_rate=loan.annual_rate,
                payment_day=loan.payment_day,
                resume_period=resume_period,
                resume_date_anchor=resume_anchor,
                mode=core_mode,
                current_payment=current_payment,
                remaining_periods_before=len(future_before),
                extra_principal=body.amount,
            )
            new_interest = sum((r.interest for r in new_rows), Decimal("0"))
            scenarios[core_mode] = PrepaymentScenarioOut(
                mode=core_mode,
                new_payment=new_rows[0].payment if new_rows else Decimal("0"),
                payoff_date=new_rows[-1].payment_date if new_rows else applied_date,
                remaining_periods=len(new_rows),
                total_interest_remaining=new_interest,
                interest_saved_vs_baseline=baseline_interest - new_interest,
            )

        return PrepaymentPreviewOut(
            loan_id=loan_id,
            as_of=applied_date,
            amount=body.amount,
            outstanding_balance_before=outstanding_balance,
            reduce_term=scenarios["reduce_term"],
            reduce_emi=scenarios["reduce_emi"],
        )

    async def apply_prepayment(self, loan_id: int, body: PrepaymentIn) -> LoanOut | None:
        """Applies a prepayment anchored at `applied_date`: historical rows on or
        before that date are left untouched, only future rows are recomputed."""
        loan = await self.session.get(Loan, loan_id)
        if loan is None:
            return None

        applied_date, future_before, outstanding_balance, resume_period, resume_anchor, \
            current_payment = await self._prepayment_context(loan, applied_date=body.applied_date)
        core_mode = _MODE_MAP.get(body.reduction_mode, "reduce_term")

        new_rows = recompute_from_midpoint(
            outstanding_balance=outstanding_balance,
            annual_rate=loan.annual_rate,
            payment_day=loan.payment_day,
            resume_period=resume_period,
            resume_date_anchor=resume_anchor,
            mode=core_mode,
            current_payment=current_payment,
            remaining_periods_before=len(future_before),
            extra_principal=body.amount,
        )

        await self.session.execute(
            delete(AmortizationRow).where(
                AmortizationRow.loan_id == loan_id,
                AmortizationRow.payment_date > applied_date,
            )
        )
        for row in new_rows:
            self.session.add(AmortizationRow(
                loan_id=loan.id,
                period=row.period,
                payment_date=row.payment_date,
                payment=row.payment,
                principal=row.principal,
                interest=row.interest,
                balance=row.balance,
            ))
        loan.extra_principal_paid += body.amount
        await self.session.flush()

        from app.domains.accounts.models import Account
        account = await self.session.get(Account, loan.account_id)
        out = LoanOut.model_validate(loan)
        out.institution = account.institution if account else None
        return out

    async def _regenerate_schedule(self, loan: Loan) -> None:
        """Delete existing rows and recompute from core (initial generation only —
        mid-loan prepayments go through apply_prepayment's anchored recompute instead)."""
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
            manual_payment=loan.manual_payment,
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

    async def _get_rows(self, loan_id: int) -> list[AmortizationRow]:
        result = await self.session.execute(
            select(AmortizationRow)
            .where(AmortizationRow.loan_id == loan_id)
            .order_by(AmortizationRow.period)
        )
        return list(result.scalars())

    @staticmethod
    def _to_core_rows(db_rows: list[AmortizationRow]) -> list[AmortRow]:
        return [
            AmortRow(
                period=r.period,
                payment_date=r.payment_date,
                payment=r.payment,
                principal=r.principal,
                interest=r.interest,
                balance=r.balance,
            )
            for r in db_rows
        ]

    async def _prepayment_context(
        self, loan: Loan, applied_date: datetime.date | None,
    ) -> tuple[
        datetime.date, list[AmortizationRow], Decimal, int, datetime.date, Decimal,
    ]:
        """Shared setup for preview/apply: resolves `applied_date`, loads the stored
        schedule, and splits it at that date. Returns
        (applied_date, future_rows, outstanding_balance, resume_period, resume_anchor,
        current_payment)."""
        resolved_date = applied_date or datetime.date.today()
        db_rows = await self._get_rows(loan.id)
        future_before, outstanding_balance, resume_period, resume_anchor = self._split_at(
            loan, db_rows, resolved_date
        )
        current_payment = future_before[0].payment if future_before else Decimal("0")
        return (
            resolved_date, future_before, outstanding_balance, resume_period, resume_anchor,
            current_payment,
        )

    @staticmethod
    def _split_at(
        loan: Loan, db_rows: list[AmortizationRow], applied_date: datetime.date,
    ) -> tuple[list[AmortizationRow], Decimal, int, datetime.date]:
        """Split the stored schedule at `applied_date`, returning
        (future_rows, outstanding_balance, resume_period, resume_anchor). Historical
        rows (payment_date <= applied_date) are intentionally not returned — callers
        must never rewrite them, only read the anchor balance/date from the last one."""
        historical = [r for r in db_rows if r.payment_date <= applied_date]
        future_before = [r for r in db_rows if r.payment_date > applied_date]
        outstanding_balance = historical[-1].balance if historical else loan.principal
        resume_period = future_before[0].period if future_before else len(historical) + 1
        resume_anchor = historical[-1].payment_date if historical else loan.start_date
        return future_before, outstanding_balance, resume_period, resume_anchor
