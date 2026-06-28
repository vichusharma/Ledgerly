"""Scenarios router — invest-vs-prepay simulator, save/compare, goal feasibility."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.domains.scenarios.schemas import (
    ScenarioCreateIn, ScenarioOut, ScenarioResultOut, ScenarioRunIn,
    GoalFeasibilityIn, GoalFeasibilityOut,
)
from app.domains.scenarios.service import ScenarioService

router = APIRouter(tags=["scenarios"], dependencies=[Depends(get_current_user)])


@router.get("/scenarios", response_model=list[ScenarioOut])
async def list_scenarios(
    compare: str | None = Query(default=None, description="Comma-separated scenario IDs"),
    db: AsyncSession = Depends(get_db),
) -> list[ScenarioOut]:
    ids = [int(i) for i in compare.split(",")] if compare else None
    return await ScenarioService(db).list_scenarios(ids=ids)


@router.post("/scenarios", response_model=ScenarioOut, status_code=201)
async def create_scenario(body: ScenarioCreateIn, db: AsyncSession = Depends(get_db)) -> ScenarioOut:
    return await ScenarioService(db).create_scenario(body)


@router.get("/scenarios/{scenario_id}", response_model=ScenarioOut)
async def get_scenario(scenario_id: int, db: AsyncSession = Depends(get_db)) -> ScenarioOut:
    obj = await ScenarioService(db).get_scenario(scenario_id)
    if obj is None:
        raise HTTPException(404, "Scenario not found")
    return obj


@router.post("/scenarios/{scenario_id}/run", response_model=ScenarioResultOut)
async def run_scenario(
    scenario_id: int,
    body: ScenarioRunIn,
    db: AsyncSession = Depends(get_db),
) -> ScenarioResultOut:
    obj = await ScenarioService(db).run_scenario(scenario_id, body)
    if obj is None:
        raise HTTPException(404, "Scenario not found")
    return obj


@router.delete("/scenarios/{scenario_id}", status_code=204)
async def delete_scenario(scenario_id: int, db: AsyncSession = Depends(get_db)) -> None:
    await ScenarioService(db).delete_scenario(scenario_id)


# ── Goal feasibility (P2) ─────────────────────────────────────────────────────

@router.post("/scenarios/goal-feasibility", response_model=GoalFeasibilityOut)
async def goal_feasibility(
    body: GoalFeasibilityIn,
    db: AsyncSession = Depends(get_db),
) -> GoalFeasibilityOut:
    return await ScenarioService(db).goal_feasibility(body)


# ── Monte Carlo projection (P3) ───────────────────────────────────────────────

from pydantic import BaseModel as _BaseModel  # noqa: E402


class MonteCarloIn(_BaseModel):
    current_value: float
    monthly_contribution: float
    annual_return_mu: float       # expected annual return (e.g. 0.07)
    annual_return_sigma: float    # annual volatility (e.g. 0.15)
    target_amount: float
    months_horizon: int
    n_paths: int = 1000


class MonteCarloOut(_BaseModel):
    p10: list[float]
    p50: list[float]
    p90: list[float]


@router.post("/scenarios/monte-carlo", response_model=MonteCarloOut)
async def run_monte_carlo(body: MonteCarloIn) -> MonteCarloOut:
    """
    P3: Run a Monte Carlo projection of portfolio value.
    Returns p10/p50/p90 percentile bands across 1000 stochastic paths.
    No DB writes — pure computation.
    """
    from app.core.projection import monte_carlo

    n_paths = min(body.n_paths, 5000)  # cap for performance
    result = monte_carlo(
        current_value=body.current_value,
        monthly_contribution=body.monthly_contribution,
        annual_return_mu=body.annual_return_mu,
        annual_return_sigma=body.annual_return_sigma,
        target_amount=body.target_amount,
        months_horizon=body.months_horizon,
        n_paths=n_paths,
    )
    return MonteCarloOut(**result)
