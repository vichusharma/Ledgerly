"""CSV import router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.domains.imports.schemas import (
    ColumnMappingIn,
    ImportBatchOut,
    ImportMappingOut,
    StatementPreviewOut,
    ValuationPreviewOut,
    ValuationSaveIn,
    ValuationSaveOut,
)
from app.domains.imports.service import ImportService

router = APIRouter(tags=["imports"], dependencies=[Depends(get_current_user)])


@router.get("/import/mappings", response_model=list[ImportMappingOut])
async def list_mappings(db: AsyncSession = Depends(get_db)) -> list[ImportMappingOut]:
    return await ImportService(db).list_mappings()


@router.post("/import/mappings", response_model=ImportMappingOut, status_code=201)
async def save_mapping(body: ColumnMappingIn, db: AsyncSession = Depends(get_db)) -> ImportMappingOut:
    return await ImportService(db).save_mapping(body)


@router.post("/imports/preview", response_model=StatementPreviewOut)
async def preview_statement(
    file: UploadFile = File(...),
    account_id: int | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
) -> StatementPreviewOut:
    """Detect format and return a preview — CSV mapping hints or parsed lines. No DB write."""
    content = await file.read()
    return await ImportService(db).preview_statement(content, file.filename, account_id)


@router.post("/imports/csv", response_model=ImportBatchOut, status_code=201)
async def import_statement(
    file: UploadFile = File(...),
    account_id: int = Form(...),
    mapping_id: int | None = Form(default=None),
    date_col: str | None = Form(default=None),
    amount_col: str | None = Form(default=None),
    debit_col: str | None = Form(default=None),
    credit_col: str | None = Form(default=None),
    desc_col: str | None = Form(default=None),
    delimiter: str | None = Form(default=None),
    date_format: str = Form(default="%d/%m/%Y"),
    decimal_separator: str = Form(default=","),
    save_as: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
) -> ImportBatchOut:
    content = await file.read()
    return await ImportService(db).import_statement(
        content=content,
        filename=file.filename or "upload.csv",
        account_id=account_id,
        mapping_id=mapping_id,
        date_col=date_col or None,
        amount_col=amount_col or None,
        debit_col=debit_col or None,
        credit_col=credit_col or None,
        desc_col=desc_col or None,
        delimiter=delimiter or None,
        date_format=date_format,
        decimal_separator=decimal_separator,
        save_as=save_as or None,
    )


@router.post("/imports/pdf-valuation/preview", response_model=ValuationPreviewOut)
async def preview_valuation(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> ValuationPreviewOut:
    """Extract candidate fund valuations from a wrapper statement PDF. No DB write."""
    content = await file.read()
    return await ImportService(db).preview_valuation(content)


@router.post("/imports/pdf-valuation", response_model=ValuationSaveOut, status_code=201)
async def save_valuation(
    body: ValuationSaveIn,
    db: AsyncSession = Depends(get_db),
) -> ValuationSaveOut:
    """Persist user-reviewed fund valuations as valuation lots + refresh snapshot."""
    return await ImportService(db).save_valuation(body)


@router.get("/imports", response_model=list[ImportBatchOut])
async def list_batches(db: AsyncSession = Depends(get_db)) -> list[ImportBatchOut]:
    return await ImportService(db).list_batches()


@router.delete("/imports/{batch_id}", status_code=204)
async def rollback_batch(batch_id: int, db: AsyncSession = Depends(get_db)) -> None:
    ok = await ImportService(db).rollback_batch(batch_id)
    if not ok:
        raise HTTPException(404, "Import batch not found")
