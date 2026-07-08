"""Tax filing router — Features J1-J6 of docs/Backlog.md (residency
profile, treaty metadata, RSU/ESPP/foreign-income/foreign-account
ingestion + manual CRUD, encrypted document access, filing-snapshot
compute/validate/lock, Cerfa-facsimile PDF generation)."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.domains.tax_filing.schemas import (
    EsppPurchaseConfirmIn,
    EsppPurchaseOut,
    EsppPurchasePreviewOut,
    FilingSnapshotOut,
    ForeignAccountCreateIn,
    ForeignAccountOut,
    ForeignAccountPreviewOut,
    ForeignAccountUpdateIn,
    ForeignIncomeCreateIn,
    ForeignIncomeOut,
    ForeignIncomePreviewOut,
    ForeignIncomeUpdateIn,
    PersonTaxResidencyOut,
    PersonTaxResidencyUpdateIn,
    RsuVestingConfirmIn,
    RsuVestingOut,
    RsuVestingPreviewOut,
    TaxDocumentOut,
    TreatyMetadataOut,
)
from app.domains.tax_filing.service import TaxFilingService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tax-filing"], dependencies=[Depends(get_current_user)])


@router.get("/tax-filing/residency/{person_id}", response_model=PersonTaxResidencyOut)
async def get_person_residency(
    person_id: int, db: AsyncSession = Depends(get_db)
) -> PersonTaxResidencyOut:
    residency = await TaxFilingService(db).get_person_residency(person_id)
    if residency is None:
        raise HTTPException(404, "Person not found")
    return residency


@router.put("/tax-filing/residency/{person_id}", response_model=PersonTaxResidencyOut)
async def set_person_residency(
    person_id: int, body: PersonTaxResidencyUpdateIn, db: AsyncSession = Depends(get_db)
) -> PersonTaxResidencyOut:
    residency = await TaxFilingService(db).set_person_residency(person_id, body)
    if residency is None:
        raise HTTPException(404, "Person not found")
    return residency


@router.get("/tax-filing/treaties", response_model=list[TreatyMetadataOut])
async def list_treaties(db: AsyncSession = Depends(get_db)) -> list[TreatyMetadataOut]:
    return await TaxFilingService(db).list_treaties()


# -- Feature J2: RSU vesting -------------------------------------------------

@router.post("/tax-filing/rsu-vesting/preview", response_model=RsuVestingPreviewOut)
async def preview_rsu_vesting(
    file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
) -> RsuVestingPreviewOut:
    content = await file.read()
    return TaxFilingService(db).preview_rsu_vesting(content)


@router.post("/tax-filing/rsu-vesting", response_model=RsuVestingOut, status_code=201)
async def confirm_rsu_vesting(
    file: UploadFile = File(...),
    payload: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> RsuVestingOut:
    content = await file.read()
    body = RsuVestingConfirmIn.model_validate_json(payload)
    return await TaxFilingService(db).confirm_rsu_vesting(
        content, original_filename=file.filename or "rsu-vesting.pdf",
        content_type=file.content_type or "application/pdf", body=body,
    )


# -- Feature J2: ESPP purchases -----------------------------------------------

@router.post("/tax-filing/espp-purchases/preview", response_model=EsppPurchasePreviewOut)
async def preview_espp_purchase(
    file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
) -> EsppPurchasePreviewOut:
    content = await file.read()
    return TaxFilingService(db).preview_espp_purchase(content)


@router.post("/tax-filing/espp-purchases", response_model=EsppPurchaseOut, status_code=201)
async def confirm_espp_purchase(
    file: UploadFile = File(...),
    payload: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> EsppPurchaseOut:
    content = await file.read()
    body = EsppPurchaseConfirmIn.model_validate_json(payload)
    return await TaxFilingService(db).confirm_espp_purchase(
        content, original_filename=file.filename or "espp-purchase.pdf",
        content_type=file.content_type or "application/pdf", body=body,
    )


# -- Feature J2: foreign income (Form 2047) ----------------------------------

@router.post("/tax-filing/foreign-income/preview", response_model=ForeignIncomePreviewOut)
async def preview_foreign_income(
    file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
) -> ForeignIncomePreviewOut:
    content = await file.read()
    return TaxFilingService(db).preview_foreign_income(content)


@router.post(
    "/tax-filing/foreign-income/confirm", response_model=ForeignIncomeOut, status_code=201
)
async def confirm_foreign_income(
    file: UploadFile = File(...),
    payload: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> ForeignIncomeOut:
    content = await file.read()
    body = ForeignIncomeCreateIn.model_validate_json(payload)
    return await TaxFilingService(db).confirm_foreign_income(
        content, original_filename=file.filename or "foreign-dividend.pdf",
        content_type=file.content_type or "application/pdf", body=body,
    )


@router.post("/tax-filing/foreign-income", response_model=ForeignIncomeOut, status_code=201)
async def create_foreign_income(
    body: ForeignIncomeCreateIn, db: AsyncSession = Depends(get_db)
) -> ForeignIncomeOut:
    """Manual entry, no source document (Feature J2-S7)."""
    return await TaxFilingService(db).create_foreign_income(body)


@router.get("/tax-filing/foreign-income", response_model=list[ForeignIncomeOut])
async def list_foreign_income(
    person_id: int | None = None,
    tax_year: int | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[ForeignIncomeOut]:
    return await TaxFilingService(db).list_foreign_income(person_id, tax_year)


@router.put("/tax-filing/foreign-income/{declaration_id}", response_model=ForeignIncomeOut)
async def update_foreign_income(
    declaration_id: int, body: ForeignIncomeUpdateIn, db: AsyncSession = Depends(get_db)
) -> ForeignIncomeOut:
    out = await TaxFilingService(db).update_foreign_income(declaration_id, body)
    if out is None:
        raise HTTPException(404, "Foreign income declaration not found")
    return out


@router.delete("/tax-filing/foreign-income/{declaration_id}", status_code=204)
async def delete_foreign_income(
    declaration_id: int, db: AsyncSession = Depends(get_db)
) -> None:
    ok = await TaxFilingService(db).delete_foreign_income(declaration_id)
    if not ok:
        raise HTTPException(404, "Foreign income declaration not found")


# -- Feature J2: foreign accounts (Form 3916) --------------------------------

@router.post("/tax-filing/foreign-accounts/preview", response_model=ForeignAccountPreviewOut)
async def preview_foreign_account(
    file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
) -> ForeignAccountPreviewOut:
    content = await file.read()
    return TaxFilingService(db).preview_foreign_account(content)


@router.post(
    "/tax-filing/foreign-accounts/confirm", response_model=ForeignAccountOut, status_code=201
)
async def confirm_foreign_account(
    file: UploadFile = File(...),
    payload: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> ForeignAccountOut:
    content = await file.read()
    body = ForeignAccountCreateIn.model_validate_json(payload)
    return await TaxFilingService(db).confirm_foreign_account(
        content, original_filename=file.filename or "foreign-bank-statement.pdf",
        content_type=file.content_type or "application/pdf", body=body,
    )


@router.post("/tax-filing/foreign-accounts", response_model=ForeignAccountOut, status_code=201)
async def create_foreign_account(
    body: ForeignAccountCreateIn, db: AsyncSession = Depends(get_db)
) -> ForeignAccountOut:
    """Manual entry, no source document (Feature J2-S7)."""
    return await TaxFilingService(db).create_foreign_account(body)


@router.get("/tax-filing/foreign-accounts", response_model=list[ForeignAccountOut])
async def list_foreign_accounts(
    person_id: int | None = None,
    tax_year: int | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[ForeignAccountOut]:
    return await TaxFilingService(db).list_foreign_accounts(person_id, tax_year)


@router.put("/tax-filing/foreign-accounts/{declaration_id}", response_model=ForeignAccountOut)
async def update_foreign_account(
    declaration_id: int, body: ForeignAccountUpdateIn, db: AsyncSession = Depends(get_db)
) -> ForeignAccountOut:
    out = await TaxFilingService(db).update_foreign_account(declaration_id, body)
    if out is None:
        raise HTTPException(404, "Foreign account declaration not found")
    return out


@router.delete("/tax-filing/foreign-accounts/{declaration_id}", status_code=204)
async def delete_foreign_account(
    declaration_id: int, db: AsyncSession = Depends(get_db)
) -> None:
    ok = await TaxFilingService(db).delete_foreign_account(declaration_id)
    if not ok:
        raise HTTPException(404, "Foreign account declaration not found")


# -- Feature J3-S3/S4: encrypted document list/download/delete --------------

@router.get("/tax-filing/documents", response_model=list[TaxDocumentOut])
async def list_documents(
    person_id: int | None = None,
    tax_year: int | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[TaxDocumentOut]:
    return await TaxFilingService(db).list_documents(person_id, tax_year)


@router.get("/tax-filing/documents/{document_id}/download")
async def download_document(
    document_id: int, db: AsyncSession = Depends(get_db)
) -> Response:
    result = await TaxFilingService(db).get_document_content(document_id)
    if result is None:
        raise HTTPException(404, "Document not found")
    meta, content = result
    # Audit trail: log the access (filename + id), never the decrypted
    # bytes or a content hash.
    logger.info(
        "tax_filing document downloaded: id=%s filename=%s", meta.id, meta.original_filename
    )
    return Response(
        content=content,
        media_type=meta.content_type,
        headers={"Content-Disposition": f'attachment; filename="{meta.original_filename}"'},
    )


@router.delete("/tax-filing/documents/{document_id}", status_code=204)
async def delete_document(document_id: int, db: AsyncSession = Depends(get_db)) -> None:
    ok = await TaxFilingService(db).delete_document(document_id)
    if not ok:
        raise HTTPException(404, "Document not found")


# -- Feature J5: FilingSnapshot compute/validate/lock ------------------------

@router.post("/tax-filing/compute", response_model=FilingSnapshotOut)
async def compute_filing(year: int, db: AsyncSession = Depends(get_db)) -> FilingSnapshotOut:
    try:
        return await TaxFilingService(db).compute_filing(year)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get("/tax-filing/forms/{year}", response_model=FilingSnapshotOut)
async def get_filing(year: int, db: AsyncSession = Depends(get_db)) -> FilingSnapshotOut:
    out = await TaxFilingService(db).get_filing(year)
    if out is None:
        raise HTTPException(404, "No filing snapshot computed for this year yet")
    return out


@router.post("/tax-filing/validate", response_model=list[str])
async def validate_filing(year: int, db: AsyncSession = Depends(get_db)) -> list[str]:
    return await TaxFilingService(db).validate_filing(year)


@router.post("/tax-filing/forms/{year}/lock", response_model=FilingSnapshotOut)
async def lock_filing(year: int, db: AsyncSession = Depends(get_db)) -> FilingSnapshotOut:
    out = await TaxFilingService(db).lock_filing(year)
    if out is None:
        raise HTTPException(404, "No filing snapshot computed for this year yet")
    return out


@router.post("/tax-filing/forms/{year}/unlock", response_model=FilingSnapshotOut)
async def unlock_filing(year: int, db: AsyncSession = Depends(get_db)) -> FilingSnapshotOut:
    out = await TaxFilingService(db).unlock_filing(year)
    if out is None:
        raise HTTPException(404, "No filing snapshot computed for this year yet")
    return out


# -- Feature J6: Cerfa-facsimile PDF generation ------------------------------

@router.post("/tax-filing/generate-pdf")
async def generate_pdf(
    year: int,
    form: str = "all",
    lock: bool = False,
    db: AsyncSession = Depends(get_db),
) -> Response:
    service = TaxFilingService(db)
    try:
        content = await service.generate_pdf(year, form)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if content is None:
        raise HTTPException(404, "No filing snapshot computed for this year yet")

    if lock:
        await service.lock_filing(year)

    if form == "all":
        media_type, filename = "application/zip", f"ledgerly_filing_{year}.zip"
    else:
        media_type, filename = "application/pdf", f"{form}_{year}.pdf"
    return Response(
        content=content, media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
