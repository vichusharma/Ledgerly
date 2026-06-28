"""Planning & goals router — goals, vacation budgets, recurring expenses."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.domains.planning.schemas import (
    GoalCreateIn, GoalOut, GoalProgressOut,
    VacationBudgetCreateIn, VacationBudgetOut, VacationBudgetUpdateIn,
    RecurringExpenseCreateIn, RecurringExpenseOut,
)
from app.domains.planning.service import PlanningService

router = APIRouter(tags=["planning"], dependencies=[Depends(get_current_user)])


# ── Goals ─────────────────────────────────────────────────────────────────────

@router.get("/goals", response_model=list[GoalOut])
async def list_goals(db: AsyncSession = Depends(get_db)) -> list[GoalOut]:
    return await PlanningService(db).list_goals()


@router.post("/goals", response_model=GoalOut, status_code=201)
async def create_goal(body: GoalCreateIn, db: AsyncSession = Depends(get_db)) -> GoalOut:
    return await PlanningService(db).create_goal(body)


@router.get("/goals/{goal_id}", response_model=GoalOut)
async def get_goal(goal_id: int, db: AsyncSession = Depends(get_db)) -> GoalOut:
    obj = await PlanningService(db).get_goal(goal_id)
    if obj is None:
        raise HTTPException(404, "Goal not found")
    return obj


@router.get("/goals/{goal_id}/progress", response_model=GoalProgressOut)
async def get_goal_progress(goal_id: int, db: AsyncSession = Depends(get_db)) -> GoalProgressOut:
    obj = await PlanningService(db).get_goal_progress(goal_id)
    if obj is None:
        raise HTTPException(404, "Goal not found")
    return obj


@router.delete("/goals/{goal_id}", status_code=204)
async def delete_goal(goal_id: int, db: AsyncSession = Depends(get_db)) -> None:
    await PlanningService(db).delete_goal(goal_id)


# ── Vacation budgets (P2) ─────────────────────────────────────────────────────

@router.get("/vacation-budgets", response_model=list[VacationBudgetOut])
async def list_vacation_budgets(db: AsyncSession = Depends(get_db)) -> list[VacationBudgetOut]:
    return await PlanningService(db).list_vacation_budgets()


@router.post("/vacation-budgets", response_model=VacationBudgetOut, status_code=201)
async def create_vacation_budget(
    body: VacationBudgetCreateIn, db: AsyncSession = Depends(get_db)
) -> VacationBudgetOut:
    return await PlanningService(db).create_vacation_budget(body)


@router.patch("/vacation-budgets/{budget_id}", response_model=VacationBudgetOut)
async def update_vacation_budget(
    budget_id: int, body: VacationBudgetUpdateIn, db: AsyncSession = Depends(get_db)
) -> VacationBudgetOut:
    obj = await PlanningService(db).update_vacation_budget(budget_id, body)
    if obj is None:
        raise HTTPException(404, "Vacation budget not found")
    return obj


# ── Recurring expenses (P2) ───────────────────────────────────────────────────

@router.get("/recurring-expenses", response_model=list[RecurringExpenseOut])
async def list_recurring_expenses(db: AsyncSession = Depends(get_db)) -> list[RecurringExpenseOut]:
    return await PlanningService(db).list_recurring_expenses()


@router.post("/recurring-expenses", response_model=RecurringExpenseOut, status_code=201)
async def create_recurring_expense(
    body: RecurringExpenseCreateIn, db: AsyncSession = Depends(get_db)
) -> RecurringExpenseOut:
    return await PlanningService(db).create_recurring_expense(body)
