"""Transactions, categories, and auto-categorization rules router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.domains.transactions.schemas import (
    CategoryCreateIn,
    CategoryOut,
    LabelCreateIn,
    LabelOut,
    RuleCreateIn,
    RuleOut,
    TransactionCreateIn,
    TransactionLabelIn,
    TransactionOut,
    TransactionSplitIn,
    TransactionUpdateIn,
)
from app.domains.transactions.service import TransactionService

router = APIRouter(tags=["transactions"], dependencies=[Depends(get_current_user)])


# ── Labels ────────────────────────────────────────────────────────────────────

@router.get("/labels", response_model=list[LabelOut])
async def list_labels(db: AsyncSession = Depends(get_db)) -> list[LabelOut]:
    return await TransactionService(db).list_labels()


@router.post("/labels", response_model=LabelOut, status_code=201)
async def create_label(body: LabelCreateIn, db: AsyncSession = Depends(get_db)) -> LabelOut:
    return await TransactionService(db).create_label(body)


@router.delete("/labels/{label_id}", status_code=204)
async def delete_label(label_id: int, db: AsyncSession = Depends(get_db)) -> None:
    await TransactionService(db).delete_label(label_id)


# ── Categories ────────────────────────────────────────────────────────────────

@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)) -> list[CategoryOut]:
    return await TransactionService(db).list_categories()


@router.post("/categories", response_model=CategoryOut, status_code=201)
async def create_category(body: CategoryCreateIn, db: AsyncSession = Depends(get_db)) -> CategoryOut:
    return await TransactionService(db).create_category(body)


@router.delete("/categories/{category_id}", status_code=204)
async def delete_category(category_id: int, db: AsyncSession = Depends(get_db)) -> None:
    await TransactionService(db).delete_category(category_id)


# ── Auto-categorization rules ─────────────────────────────────────────────────

@router.get("/rules", response_model=list[RuleOut])
async def list_rules(db: AsyncSession = Depends(get_db)) -> list[RuleOut]:
    return await TransactionService(db).list_rules()


@router.post("/rules", response_model=RuleOut, status_code=201)
async def create_rule(body: RuleCreateIn, db: AsyncSession = Depends(get_db)) -> RuleOut:
    return await TransactionService(db).create_rule(body)


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_rule(rule_id: int, db: AsyncSession = Depends(get_db)) -> None:
    await TransactionService(db).delete_rule(rule_id)


# ── Transactions ──────────────────────────────────────────────────────────────

@router.get("/transactions", response_model=list[TransactionOut])
async def list_transactions(
    account_id: int | None = Query(default=None),
    scope: str = "household",
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
    category_id: int | None = Query(default=None),
    limit: int = 200,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
) -> list[TransactionOut]:
    return await TransactionService(db).list_transactions(
        account_id=account_id,
        scope=scope,
        from_date=from_date,
        to_date=to_date,
        category_id=category_id,
        limit=limit,
        offset=offset,
    )


@router.post("/transactions", response_model=TransactionOut, status_code=201)
async def create_transaction(
    body: TransactionCreateIn, db: AsyncSession = Depends(get_db)
) -> TransactionOut:
    return await TransactionService(db).create_transaction(body)


@router.patch("/transactions/{txn_id}", response_model=TransactionOut)
async def update_transaction(
    txn_id: int, body: TransactionUpdateIn, db: AsyncSession = Depends(get_db)
) -> TransactionOut:
    obj = await TransactionService(db).update_transaction(txn_id, body)
    if obj is None:
        raise HTTPException(404, "Transaction not found")
    return obj


@router.post("/transactions/{txn_id}/split", response_model=list[TransactionOut], status_code=201)
async def split_transaction(
    txn_id: int, body: TransactionSplitIn, db: AsyncSession = Depends(get_db)
) -> list[TransactionOut]:
    return await TransactionService(db).split_transaction(txn_id, body)


@router.put("/transactions/{txn_id}/labels", response_model=TransactionOut)
async def set_transaction_labels(
    txn_id: int, body: TransactionLabelIn, db: AsyncSession = Depends(get_db)
) -> TransactionOut:
    obj = await TransactionService(db).set_transaction_labels(txn_id, body.label_ids)
    if obj is None:
        raise HTTPException(404, "Transaction not found")
    return obj


@router.delete("/transactions/{txn_id}", status_code=204)
async def delete_transaction(txn_id: int, db: AsyncSession = Depends(get_db)) -> None:
    await TransactionService(db).delete_transaction(txn_id)
