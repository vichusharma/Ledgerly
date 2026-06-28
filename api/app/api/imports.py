"""CSV import router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.domains.imports.schemas import (
    ColumnMappingIn, ImportBatchOut, ImportMappingOut,
)
from app.domains.imports.service import ImportService

router = APIRouter(tags=["imports"], dependencies=[Depends(get_current_user)])


@router.get("/import/mappings", response_model=list[ImportMappingOut])
async def list_mappings(db: AsyncSession = Depends(get_db)) -> list[ImportMappingOut]:
    return await ImportService(db).list_mappings()


@router.post("/import/mappings", response_model=ImportMappingOut, status_code=201)
async def save_mapping(body: ColumnMappingIn, db: AsyncSession = Depends(get_db)) -> ImportMappingOut:
    return await ImportService(db).save_mapping(body)


@router.post("/imports/csv", response_model=ImportBatchOut)
async def import_csv(
    file: UploadFile = File(...),
    account_id: int = Form(...),
    mapping_id: int | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
) -> ImportBatchOut:
    content = await file.read()
    return await ImportService(db).import_csv(
        content=content,
        filename=file.filename or "upload.csv",
        account_id=account_id,
        mapping_id=mapping_id,
    )


@router.get("/imports", response_model=list[ImportBatchOut])
async def list_batches(db: AsyncSession = Depends(get_db)) -> list[ImportBatchOut]:
    return await ImportService(db).list_batches()


@router.delete("/imports/{batch_id}", status_code=204)
async def rollback_batch(batch_id: int, db: AsyncSession = Depends(get_db)) -> None:
    """P2: rollback an import batch — removes all its transactions."""
    ok = await ImportService(db).rollback_batch(batch_id)
    if not ok:
        raise HTTPException(404, "Import batch not found")
