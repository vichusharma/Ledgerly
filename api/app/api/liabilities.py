"""Liabilities router — loans, amortization, debt view."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.domains.liabilities.schemas import (
    AmortRowOut, DebtSummaryOut, LoanCreateIn, LoanOut, LoanUpdateIn,
    PrepaymentIn, PrepaymentPreviewOut,
)
from app.domains.liabilities.service import LiabilityService

router = APIRouter(tags=["liabilities"], dependencies=[Depends(get_current_user)])


@router.get("/liabilities", response_model=list[LoanOut])
async def list_loans(db: AsyncSession = Depends(get_db)) -> list[LoanOut]:
    return await LiabilityService(db).list_loans()


@router.post("/liabilities", response_model=LoanOut, status_code=201)
async def create_loan(body: LoanCreateIn, db: AsyncSession = Depends(get_db)) -> LoanOut:
    try:
        return await LiabilityService(db).create_loan(body)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e


@router.get("/liabilities/{loan_id}", response_model=LoanOut)
async def get_loan(loan_id: int, db: AsyncSession = Depends(get_db)) -> LoanOut:
    obj = await LiabilityService(db).get_loan(loan_id)
    if obj is None:
        raise HTTPException(404, "Loan not found")
    return obj


@router.patch("/liabilities/{loan_id}", response_model=LoanOut)
async def update_loan(
    loan_id: int, body: LoanUpdateIn, db: AsyncSession = Depends(get_db)
) -> LoanOut:
    obj = await LiabilityService(db).update_loan(loan_id, body)
    if obj is None:
        raise HTTPException(404, "Loan not found")
    return obj


@router.delete("/liabilities/{loan_id}", status_code=204)
async def delete_loan(loan_id: int, db: AsyncSession = Depends(get_db)) -> None:
    await LiabilityService(db).delete_loan(loan_id)


@router.get("/liabilities/{loan_id}/schedule", response_model=list[AmortRowOut])
async def get_amortization_schedule(
    loan_id: int, db: AsyncSession = Depends(get_db)
) -> list[AmortRowOut]:
    rows = await LiabilityService(db).get_schedule(loan_id)
    if rows is None:
        raise HTTPException(404, "Loan not found")
    return rows


@router.get("/liabilities/{loan_id}/summary", response_model=DebtSummaryOut)
async def get_debt_summary(loan_id: int, db: AsyncSession = Depends(get_db)) -> DebtSummaryOut:
    obj = await LiabilityService(db).get_debt_summary(loan_id)
    if obj is None:
        raise HTTPException(404, "Loan not found")
    return obj


@router.post("/liabilities/{loan_id}/prepay/preview", response_model=PrepaymentPreviewOut)
async def preview_prepayment(
    loan_id: int, body: PrepaymentIn, db: AsyncSession = Depends(get_db)
) -> PrepaymentPreviewOut:
    """Non-destructive: computes both reduce-term and reduce-EMI scenarios."""
    try:
        obj = await LiabilityService(db).preview_prepayment(loan_id, body)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    if obj is None:
        raise HTTPException(404, "Loan not found")
    return obj


@router.post("/liabilities/{loan_id}/prepay", response_model=LoanOut)
async def apply_prepayment(
    loan_id: int, body: PrepaymentIn, db: AsyncSession = Depends(get_db)
) -> LoanOut:
    """P2: apply a partial prepayment and recompute the schedule from applied_date."""
    try:
        obj = await LiabilityService(db).apply_prepayment(loan_id, body)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    if obj is None:
        raise HTTPException(404, "Loan not found")
    return obj
