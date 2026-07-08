"""Planning service — goals, vacation budgets, recurring expenses, GDPR."""
from __future__ import annotations

import csv
import io
import json
import zipfile
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.planning.models import Goal, RecurringExpense, VacationBudget
from app.domains.planning.schemas import (
    GoalCreateIn, GoalOut, GoalProgressOut,
    RecurringExpenseCreateIn, RecurringExpenseOut,
    VacationBudgetCreateIn, VacationBudgetOut, VacationBudgetUpdateIn,
)


class PlanningService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Goals ─────────────────────────────────────────────────────────────

    async def list_goals(self) -> list[GoalOut]:
        result = await self.session.execute(select(Goal))
        return [GoalOut.model_validate(g) for g in result.scalars()]

    async def get_goal(self, goal_id: int) -> GoalOut | None:
        g = await self.session.get(Goal, goal_id)
        return GoalOut.model_validate(g) if g else None

    async def create_goal(self, body: GoalCreateIn) -> GoalOut:
        g = Goal(**body.model_dump())
        self.session.add(g)
        await self.session.flush()
        return GoalOut.model_validate(g)

    async def delete_goal(self, goal_id: int) -> None:
        g = await self.session.get(Goal, goal_id)
        if g:
            await self.session.delete(g)

    async def get_goal_progress(self, goal_id: int) -> GoalProgressOut | None:
        g = await self.session.get(Goal, goal_id)
        if g is None:
            return None

        # Current value = current household net worth (simplified; for FI goals)
        from app.domains.networth.service import NetWorthService
        nw = await NetWorthService(self.session).get_networth()
        current_value = nw.current

        progress_pct = (
            float(current_value / g.target_amount * 100)
            if g.target_amount > Decimal("0")
            else 0.0
        )

        # Goal feasibility projection
        projected_reach_date = None
        on_track = current_value >= g.target_amount

        if g.target_date and not on_track:
            from app.core.projection import goal_feasibility
            result = goal_feasibility(
                current_value=current_value,
                monthly_contribution=Decimal("1000"),  # TODO: from user settings
                annual_return=Decimal("0.05"),
                target_amount=g.target_amount,
                target_date=g.target_date,
            )
            on_track = result.on_track
            projected_reach_date = result.projected_reach_date

        if current_value >= g.target_amount:
            g.is_achieved = True
            await self.session.flush()

        return GoalProgressOut(
            goal_id=goal_id,
            current_value=current_value,
            target_amount=g.target_amount,
            progress_pct=min(progress_pct, 100.0),
            on_track=on_track,
            projected_reach_date=projected_reach_date,
        )

    # ── Vacation budgets ──────────────────────────────────────────────────

    async def list_vacation_budgets(self) -> list[VacationBudgetOut]:
        result = await self.session.execute(select(VacationBudget))
        budgets = list(result.scalars())
        out = []
        for b in budgets:
            base = VacationBudgetOut.model_validate(b)
            base = base.model_copy(update={
                "planned_total": sum(
                    Decimal(str(item.get("amount", 0))) for item in (b.planned_items or [])
                ),
                "actual_total": await self._get_vacation_actuals(b.id),
            })
            out.append(base)
        return out

    async def create_vacation_budget(self, body: VacationBudgetCreateIn) -> VacationBudgetOut:
        b = VacationBudget(**body.model_dump())
        self.session.add(b)
        await self.session.flush()
        return VacationBudgetOut.model_validate(b)

    async def update_vacation_budget(
        self, budget_id: int, body: VacationBudgetUpdateIn
    ) -> VacationBudgetOut | None:
        b = await self.session.get(VacationBudget, budget_id)
        if b is None:
            return None
        if body.planned_items is not None:
            b.planned_items = body.planned_items
        if body.notes is not None:
            b.notes = body.notes
        await self.session.flush()
        return VacationBudgetOut.model_validate(b)

    async def _get_vacation_actuals(self, budget_id: int) -> Decimal:
        from app.domains.transactions.models import Transaction
        result = await self.session.execute(
            select(Transaction).where(Transaction.vacation_budget_id == budget_id)
        )
        return sum(
            (abs(t.amount) for t in result.scalars()),
            Decimal("0"),
        )

    # ── Recurring expenses ────────────────────────────────────────────────

    async def list_recurring_expenses(self) -> list[RecurringExpenseOut]:
        result = await self.session.execute(select(RecurringExpense))
        return [RecurringExpenseOut.model_validate(r) for r in result.scalars()]

    async def create_recurring_expense(
        self, body: RecurringExpenseCreateIn
    ) -> RecurringExpenseOut:
        r = RecurringExpense(**body.model_dump())
        self.session.add(r)
        await self.session.flush()
        return RecurringExpenseOut.model_validate(r)

    # ── GDPR ─────────────────────────────────────────────────────────────

    async def export_all_data(self) -> bytes:
        """Full GDPR export — returns a ZIP containing JSON/CSV of all data."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            # Accounts
            from app.domains.accounts.models import Account, Person
            persons = list((await self.session.execute(select(Person))).scalars())
            zf.writestr(
                "persons.json",
                json.dumps([{"id": p.id, "name": p.name} for p in persons], default=str),
            )
            accounts = list((await self.session.execute(select(Account))).scalars())
            zf.writestr(
                "accounts.json",
                json.dumps(
                    [{"id": a.id, "name": a.name, "type": str(a.type)} for a in accounts],
                    default=str,
                ),
            )
            # Transactions as CSV
            from app.domains.transactions.models import Transaction
            txns = list((await self.session.execute(select(Transaction))).scalars())
            csv_buf = io.StringIO()
            writer = csv.writer(csv_buf)
            writer.writerow(["id", "account_id", "date", "amount", "description", "category_id"])
            for t in txns:
                writer.writerow([t.id, t.account_id, t.date, t.amount, t.description, t.category_id])
            zf.writestr("transactions.csv", csv_buf.getvalue())

            # Goals
            goals = list((await self.session.execute(select(Goal))).scalars())
            zf.writestr(
                "goals.json",
                json.dumps(
                    [{"id": g.id, "name": g.name, "target": str(g.target_amount)} for g in goals],
                    default=str,
                ),
            )

            # Payslips (Epic I)
            from app.domains.salary.models import Payslip
            payslips = list((await self.session.execute(select(Payslip))).scalars())
            zf.writestr(
                "payslips.json",
                json.dumps(
                    [
                        {
                            "id": p.id, "person_id": p.person_id,
                            "pay_period": p.pay_period, "employer": p.employer,
                            "gross": p.gross, "net_taxable": p.net_taxable,
                            "net_paid": p.net_paid,
                        }
                        for p in payslips
                    ],
                    default=str,
                ),
            )

            # Household tax settings (Epic I) — personal (filing status +
            # dependents choice), unlike `tax_year_configs` below.
            from app.domains.tax.models import HouseholdTaxDependent, HouseholdTaxSettings
            settings_rows = list(
                (await self.session.execute(select(HouseholdTaxSettings))).scalars()
            )
            dependent_rows = list(
                (await self.session.execute(select(HouseholdTaxDependent))).scalars()
            )
            zf.writestr(
                "household_tax_settings.json",
                json.dumps(
                    {
                        "settings": [
                            {"id": s.id, "filing_status": str(s.filing_status)}
                            for s in settings_rows
                        ],
                        "dependents": [
                            {
                                "household_tax_settings_id": d.household_tax_settings_id,
                                "person_id": d.person_id,
                            }
                            for d in dependent_rows
                        ],
                    },
                    default=str,
                ),
            )

            # Epic J — tax filing (residency, foreign income/accounts,
            # encrypted source documents). `treaty_metadata` is seeded
            # reference data (the same for every user, not personal), so
            # it's intentionally excluded here, same as `tax_year_configs`.
            from app.domains.tax_filing.models import (
                ForeignAccountDeclaration,
                ForeignIncomeDeclaration,
                PersonTaxResidency,
                TaxDocument,
            )
            from app.infra.document_crypto import decrypt_bytes

            residencies = list(
                (await self.session.execute(select(PersonTaxResidency))).scalars()
            )
            zf.writestr(
                "person_tax_residency.json",
                json.dumps(
                    [
                        {
                            "person_id": r.person_id,
                            "home_country_code": r.home_country_code,
                            "home_country_tax_id": r.home_country_tax_id,
                            "french_tax_number": r.french_tax_number,
                        }
                        for r in residencies
                    ],
                    default=str,
                ),
            )
            foreign_income = list(
                (await self.session.execute(select(ForeignIncomeDeclaration))).scalars()
            )
            zf.writestr(
                "foreign_income_declarations.json",
                json.dumps(
                    [
                        {
                            "id": r.id, "person_id": r.person_id, "tax_year": r.tax_year,
                            "income_type": str(r.income_type),
                            "source_country_code": r.source_country_code,
                            "source_description": r.source_description,
                            "gross_amount_eur": r.gross_amount_eur,
                        }
                        for r in foreign_income
                    ],
                    default=str,
                ),
            )
            foreign_accounts = list(
                (await self.session.execute(select(ForeignAccountDeclaration))).scalars()
            )
            zf.writestr(
                "foreign_account_declarations.json",
                json.dumps(
                    [
                        {
                            "id": r.id, "person_id": r.person_id, "tax_year": r.tax_year,
                            "bank_name": r.bank_name, "country_code": r.country_code,
                            "account_identifier_masked": r.account_identifier_masked,
                        }
                        for r in foreign_accounts
                    ],
                    default=str,
                ),
            )
            documents = list((await self.session.execute(select(TaxDocument))).scalars())
            zf.writestr(
                "tax_documents/manifest.json",
                json.dumps(
                    [
                        {
                            "id": d.id, "document_type": str(d.document_type),
                            "original_filename": d.original_filename,
                            "uploaded_at": d.uploaded_at,
                        }
                        for d in documents
                    ],
                    default=str,
                ),
            )
            for d in documents:
                # Decrypted at export time — the export itself is the
                # user's own copy of their data, not at-rest storage.
                zf.writestr(
                    f"tax_documents/{d.id}_{d.original_filename}",
                    decrypt_bytes(d.encrypted_content),
                )
        return buf.getvalue()

    async def erase_all_data(self) -> None:
        """GDPR hard erase — cascade-deletes all personal financial data.

        Seeded reference tables (`tax_year_configs`, `treaty_metadata`)
        are deliberately excluded — they're the same barème/treaty data
        for every user, not personal data, and erasing them would just
        require a reseed rather than protecting anyone's privacy.
        """
        from sqlalchemy import text
        for table in [
            "account_snapshots", "amortization_rows", "investment_lots",
            # `vesting_schedules` predates this session (Feature P2) but
            # was never added here either — a pre-existing gap, only
            # load-bearing now that Feature J2 is its first real writer
            # (it holds RSU grant details, genuinely personal data).
            # Deleted after `investment_lots` since lots FK to it.
            "vesting_schedules",
            "instrument_prices", "transactions", "import_batches",
            "loans", "scenarios", "goals", "vacation_budgets",
            "recurring_expenses",
            # Epic I (payslip/tax-estimate) — previously missing from
            # this list entirely.
            "payslips", "household_tax_dependents", "household_tax_settings",
            # Epic J (tax filing) — new this session.
            "tax_documents", "foreign_account_declarations",
            "foreign_income_declarations", "person_tax_residency",
            "accounts", "persons",
        ]:
            await self.session.execute(text(f"DELETE FROM {table}"))
        await self.session.flush()
