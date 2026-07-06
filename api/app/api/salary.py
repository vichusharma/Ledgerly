"""Payslip ingestion router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.domains.salary.schemas import PayslipConfirmIn, PayslipOut, PayslipPreviewOut
from app.domains.salary.service import SalaryService

router = APIRouter(tags=["salary"], dependencies=[Depends(get_current_user)])


@router.post("/salary/payslips/preview", response_model=PayslipPreviewOut)
async def preview_payslip(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> PayslipPreviewOut:
    """Extract candidate fields from a payslip PDF. No DB write."""
    content = await file.read()
    return await SalaryService(db).preview_payslip(content)


@router.post("/salary/payslips", response_model=PayslipOut, status_code=201)
async def save_payslip(body: PayslipConfirmIn, db: AsyncSession = Depends(get_db)) -> PayslipOut:
    """Persist the reviewed payslip — upserts by (person_id, pay_period)."""
    return await SalaryService(db).save_payslip(body)


@router.get("/salary/payslips", response_model=list[PayslipOut])
async def list_payslips(
    person_id: int | None = None,
    year: int | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[PayslipOut]:
    return await SalaryService(db).list_payslips(person_id, year)


@router.delete("/salary/payslips/{payslip_id}", status_code=204)
async def delete_payslip(payslip_id: int, db: AsyncSession = Depends(get_db)) -> None:
    ok = await SalaryService(db).delete_payslip(payslip_id)
    if not ok:
        raise HTTPException(404, "Payslip not found")
