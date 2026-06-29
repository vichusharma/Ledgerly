"""Transactions service — categories, rules, CRUD."""
from __future__ import annotations

import re

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.transactions.models import Category, CategoryRule, Label, Transaction
from app.domains.transactions.schemas import (
    CategoryCreateIn,
    CategoryOut,
    LabelCreateIn,
    LabelOut,
    RuleCreateIn,
    RuleOut,
    TransactionCreateIn,
    TransactionOut,
    TransactionSplitIn,
    TransactionUpdateIn,
)


class TransactionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Labels ────────────────────────────────────────────────────────────

    async def list_labels(self) -> list[LabelOut]:
        result = await self.session.execute(select(Label).order_by(Label.name))
        return [LabelOut.model_validate(lb) for lb in result.scalars()]

    async def create_label(self, body: LabelCreateIn) -> LabelOut:
        lb = Label(name=body.name, color=body.color)
        self.session.add(lb)
        await self.session.flush()
        return LabelOut.model_validate(lb)

    async def delete_label(self, label_id: int) -> None:
        lb = await self.session.get(Label, label_id)
        if lb:
            await self.session.delete(lb)

    async def set_transaction_labels(
        self, txn_id: int, label_ids: list[int]
    ) -> TransactionOut | None:
        from sqlalchemy.orm import selectinload
        opts = [selectinload(Transaction.labels)]
        txn = await self.session.get(Transaction, txn_id, options=opts)
        if txn is None:
            return None
        if label_ids:
            result = await self.session.execute(select(Label).where(Label.id.in_(label_ids)))
            txn.labels = list(result.scalars())
        else:
            txn.labels = []
        await self.session.flush()
        return TransactionOut.model_validate(txn)

    # ── Categories ────────────────────────────────────────────────────────

    async def list_categories(self) -> list[CategoryOut]:
        result = await self.session.execute(select(Category).order_by(Category.name))
        return [CategoryOut.model_validate(c) for c in result.scalars()]

    async def create_category(self, body: CategoryCreateIn) -> CategoryOut:
        cat = Category(name=body.name, parent_id=body.parent_id, color=body.color)
        self.session.add(cat)
        await self.session.flush()
        return CategoryOut.model_validate(cat)

    async def delete_category(self, category_id: int) -> None:
        await self.session.execute(delete(Category).where(Category.id == category_id))

    # ── Rules ─────────────────────────────────────────────────────────────

    async def list_rules(self) -> list[RuleOut]:
        result = await self.session.execute(
            select(CategoryRule).order_by(CategoryRule.priority.desc())
        )
        return [RuleOut.model_validate(r) for r in result.scalars()]

    async def create_rule(self, body: RuleCreateIn) -> RuleOut:
        # Validate regex compiles
        try:
            re.compile(body.pattern)
        except re.error as exc:
            raise ValueError(f"Invalid regex pattern: {exc}") from exc

        rule = CategoryRule(
            pattern=body.pattern,
            category_id=body.category_id,
            account_id=body.account_id,
            priority=body.priority,
        )
        self.session.add(rule)
        await self.session.flush()
        return RuleOut.model_validate(rule)

    async def delete_rule(self, rule_id: int) -> None:
        await self.session.execute(delete(CategoryRule).where(CategoryRule.id == rule_id))

    # ── Auto-categorize ───────────────────────────────────────────────────

    async def _get_rules(self) -> list[CategoryRule]:
        result = await self.session.execute(
            select(CategoryRule).order_by(CategoryRule.priority.desc())
        )
        return list(result.scalars())

    def _auto_categorize(self, description: str, rules: list[CategoryRule]) -> int | None:
        for rule in rules:
            if re.search(rule.pattern, description, re.IGNORECASE):
                return rule.category_id
        return None

    # ── Transactions ──────────────────────────────────────────────────────

    async def list_transactions(
        self,
        account_id: int | None = None,
        scope: str = "household",
        from_date: str | None = None,
        to_date: str | None = None,
        category_id: int | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[TransactionOut]:
        stmt = select(Transaction).where(Transaction.parent_id.is_(None))
        if account_id:
            stmt = stmt.where(Transaction.account_id == account_id)
        if from_date:
            import datetime
            stmt = stmt.where(Transaction.date >= datetime.date.fromisoformat(from_date))
        if to_date:
            import datetime
            stmt = stmt.where(Transaction.date <= datetime.date.fromisoformat(to_date))
        if category_id:
            stmt = stmt.where(Transaction.category_id == category_id)
        stmt = stmt.order_by(Transaction.date.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return [TransactionOut.model_validate(t) for t in result.scalars()]

    async def create_transaction(self, body: TransactionCreateIn) -> TransactionOut:
        rules = await self._get_rules()
        category_id = body.category_id or self._auto_categorize(body.description, rules)
        dedup_hash = Transaction.compute_hash(
            body.account_id, body.date, body.amount, body.description
        )
        txn = Transaction(
            account_id=body.account_id,
            date=body.date,
            amount=body.amount,
            currency=body.currency,
            description=body.description,
            category_id=category_id,
            dedup_hash=dedup_hash,
        )
        self.session.add(txn)
        await self.session.flush()
        return TransactionOut.model_validate(txn)

    async def update_transaction(
        self, txn_id: int, body: TransactionUpdateIn
    ) -> TransactionOut | None:
        txn = await self.session.get(Transaction, txn_id)
        if txn is None:
            return None
        updates = body.model_dump(exclude_none=True)
        for k, v in updates.items():
            setattr(txn, k, v)
        await self.session.flush()
        return TransactionOut.model_validate(txn)

    async def split_transaction(
        self, txn_id: int, body: TransactionSplitIn
    ) -> list[TransactionOut]:
        """Split a transaction into sub-transactions."""
        parent = await self.session.get(Transaction, txn_id)
        if parent is None:
            raise ValueError("Transaction not found")

        total = sum(s.amount for s in body.splits)
        if abs(float(total) - float(parent.amount)) > 0.01:
            raise ValueError(
                f"Split amounts ({total}) must sum to original amount ({parent.amount})"
            )

        parent.is_split = True
        splits: list[Transaction] = []
        for line in body.splits:
            dedup_hash = Transaction.compute_hash(
                parent.account_id, parent.date, line.amount,
                f"{parent.description}|split|{line.description}"
            )
            child = Transaction(
                account_id=parent.account_id,
                date=parent.date,
                amount=line.amount,
                currency=parent.currency,
                description=line.description or parent.description,
                category_id=line.category_id,
                dedup_hash=dedup_hash,
                parent_id=parent.id,
                import_batch_id=parent.import_batch_id,
            )
            self.session.add(child)
            splits.append(child)

        await self.session.flush()
        return [TransactionOut.model_validate(s) for s in splits]

    async def delete_transaction(self, txn_id: int) -> None:
        txn = await self.session.get(Transaction, txn_id)
        if txn:
            await self.session.delete(txn)
