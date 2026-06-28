"""Scenarios service — invest-vs-prepay + goal feasibility."""
from __future__ import annotations

import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.projection import goal_feasibility
from app.core.simulation import invest_vs_prepay
from app.domains.liabilities.models import AmortizationRow, Loan
from app.domains.scenarios.models import Scenario, ScenarioType
from app.domains.scenarios.schemas import (
    GoalFeasibilityIn, GoalFeasibilityOut,
    MonthPoint, ReturnScenario, ScenarioCreateIn, ScenarioOut,
    ScenarioResultOut, ScenarioRunIn,
)


class ScenarioService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_scenarios(self, ids: list[int] | None = None) -> list[ScenarioOut]:
        stmt = select(Scenario).order_by(Scenario.created_at.desc())
        if ids:
            stmt = stmt.where(Scenario.id.in_(ids))
        result = await self.session.execute(stmt)
        return [ScenarioOut.model_validate(s) for s in result.scalars()]

    async def get_scenario(self, scenario_id: int) -> ScenarioOut | None:
        s = await self.session.get(Scenario, scenario_id)
        return ScenarioOut.model_validate(s) if s else None

    async def create_scenario(self, body: ScenarioCreateIn) -> ScenarioOut:
        s = Scenario(
            name=body.name,
            type=body.type,
            parameters=body.parameters,
            notes=body.notes,
            created_at=datetime.datetime.utcnow(),
        )
        self.session.add(s)
        await self.session.flush()
        return ScenarioOut.model_validate(s)

    async def delete_scenario(self, scenario_id: int) -> None:
        s = await self.session.get(Scenario, scenario_id)
        if s:
            await self.session.delete(s)

    async def run_scenario(
        self, scenario_id: int, body: ScenarioRunIn
    ) -> ScenarioResultOut | None:
        scenario = await self.session.get(Scenario, scenario_id)
        if scenario is None:
            return None

        # Load mortgage if provided
        mortgage_principal = Decimal("0")
        mortgage_rate = Decimal("0")
        mortgage_remaining_months = body.horizon_months
        mortgage_start_date = datetime.date.today()

        if body.mortgage_id:
            loan = await self.session.get(Loan, body.mortgage_id)
            if loan:
                # Compute remaining months from schedule
                rows_result = await self.session.execute(
                    select(AmortizationRow)
                    .where(
                        AmortizationRow.loan_id == loan.id,
                        AmortizationRow.payment_date > datetime.date.today(),
                    )
                )
                future_rows = list(rows_result.scalars())
                mortgage_principal = future_rows[0].balance if future_rows else loan.principal
                mortgage_rate = loan.annual_rate
                mortgage_remaining_months = len(future_rows) or loan.term_months
                mortgage_start_date = loan.start_date

        returns = {
            "low": body.returns.low,
            "base": body.returns.base,
            "high": body.returns.high,
        }

        sim_results = invest_vs_prepay(
            lump_sum=body.lump_sum,
            monthly_extra=body.monthly,
            horizon_months=body.horizon_months,
            mortgage_principal=mortgage_principal,
            annual_mortgage_rate=mortgage_rate,
            mortgage_remaining_months=mortgage_remaining_months,
            mortgage_start_date=mortgage_start_date,
            returns=returns,
        )

        results_by_label: dict[str, ReturnScenario] = {}
        for r in sim_results:
            series = [
                MonthPoint(month=p.month, invest=p.invest, prepay=p.prepay, delta=p.delta)
                for p in r.series
            ]
            results_by_label[r.return_label] = ReturnScenario(
                return_label=r.return_label,
                annual_return=r.annual_return,
                invest_net_worth_end=r.invest_net_worth_end,
                prepay_net_worth_end=r.prepay_net_worth_end,
                delta_end=r.delta_end,
                breakeven_month=r.breakeven_month,
                interest_saved_if_prepay=r.interest_saved_if_prepay,
                interpretation=r.interpretation,
                series=series,
            )

        # Cache result
        scenario.last_result = {k: v.model_dump() for k, v in results_by_label.items()}
        scenario.last_run_at = datetime.datetime.utcnow()
        await self.session.flush()

        return ScenarioResultOut(
            scenario_id=scenario_id,
            currency="EUR",
            results=results_by_label,
        )

    async def goal_feasibility(self, body: GoalFeasibilityIn) -> GoalFeasibilityOut:
        result = goal_feasibility(
            current_value=body.current_value,
            monthly_contribution=body.monthly_contribution,
            annual_return=body.annual_return,
            target_amount=body.target_amount,
            target_date=body.target_date,
        )
        return GoalFeasibilityOut(
            projected_value_at_target=result.projected_value_at_target,
            on_track=result.on_track,
            projected_reach_date=result.projected_reach_date,
            required_annual_return=result.required_annual_return,
            months_to_target=result.months_to_target,
        )
