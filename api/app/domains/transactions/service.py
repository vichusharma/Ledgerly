"""Transactions service — categories, rules, CRUD."""
from __future__ import annotations

import datetime
import re
from collections import defaultdict
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.transactions.merchant import normalize_merchant
from app.domains.transactions.models import Category, CategoryRule, Label, Transaction
from app.domains.transactions.schemas import (
    AnalyticsOut,
    CategoryBucket,
    CategoryCreateIn,
    CategoryOut,
    LabelCreateIn,
    LabelOut,
    MerchantBucket,
    MonthBucket,
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

    # ── Analytics ─────────────────────────────────────────────────────────

    def _analytics_filters(
        self,
        account_id: int | None,
        from_date: str | None,
        to_date: str | None,
    ) -> list:
        """Shared WHERE clauses for every analytics aggregate."""
        clauses = [Transaction.parent_id.is_(None)]
        if account_id:
            clauses.append(Transaction.account_id == account_id)
        if from_date:
            clauses.append(Transaction.date >= datetime.date.fromisoformat(from_date))
        if to_date:
            clauses.append(Transaction.date <= datetime.date.fromisoformat(to_date))
        return clauses

    async def get_analytics(
        self,
        from_date: str | None = None,
        to_date: str | None = None,
        account_id: int | None = None,
        scope: str = "household",
    ) -> AnalyticsOut:
        where = self._analytics_filters(account_id, from_date, to_date)
        spent_expr = func.sum(
            func.coalesce(func.abs(func.least(Transaction.amount, 0)), 0)
        )
        income_expr = func.sum(func.greatest(Transaction.amount, 0))

        # ── Totals ──
        totals = (await self.session.execute(
            select(spent_expr, income_expr, func.count()).where(*where)
        )).one()
        total_spent = Decimal(totals[0] or 0)
        total_income = Decimal(totals[1] or 0)
        txn_count = int(totals[2] or 0)

        # ── By month ──
        month_col = func.to_char(Transaction.date, "YYYY-MM")
        month_rows = (await self.session.execute(
            select(month_col.label("m"), spent_expr, income_expr)
            .where(*where)
            .group_by("m")
            .order_by("m")
        )).all()
        by_month = [
            MonthBucket(month=r[0], spent=Decimal(r[1] or 0), income=Decimal(r[2] or 0))
            for r in month_rows
        ]

        # ── By category (debits only) ──
        cat_rows = (await self.session.execute(
            select(
                Transaction.category_id,
                Category.name,
                Category.color,
                spent_expr,
            )
            .select_from(Transaction)
            .outerjoin(Category, Category.id == Transaction.category_id)
            .where(*where, Transaction.amount < 0)
            .group_by(Transaction.category_id, Category.name, Category.color)
            .order_by(spent_expr.desc())
        )).all()
        by_category = [
            CategoryBucket(
                category_id=r[0],
                name=r[1] or "Uncategorized",
                color=r[2],
                spent=Decimal(r[3] or 0),
                pct=float(Decimal(r[3] or 0) / total_spent * 100) if total_spent else 0.0,
            )
            for r in cat_rows
        ]

        # ── Top merchants (group raw descriptions in SQL, normalize in Python) ──
        desc_rows = (await self.session.execute(
            select(Transaction.description, spent_expr, func.count())
            .where(*where, Transaction.amount < 0)
            .group_by(Transaction.description)
        )).all()
        merged: dict[str, dict] = defaultdict(lambda: {"spent": Decimal(0), "count": 0})
        for desc, spent, count in desc_rows:
            key = normalize_merchant(desc or "")
            merged[key]["spent"] += Decimal(spent or 0)
            merged[key]["count"] += int(count or 0)
        top_merchants = [
            MerchantBucket(merchant=k, spent=v["spent"], count=v["count"])
            for k, v in sorted(merged.items(), key=lambda kv: kv[1]["spent"], reverse=True)
        ][:10]

        return AnalyticsOut(
            total_spent=total_spent,
            total_income=total_income,
            net=total_income - total_spent,
            txn_count=txn_count,
            by_month=by_month,
            by_category=by_category,
            top_merchants=top_merchants,
        )

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
        await self.session.refresh(txn, ["labels"])
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
        await self.session.refresh(txn, ["labels"])
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
        for s in splits:
            await self.session.refresh(s, ["labels"])
        return [TransactionOut.model_validate(s) for s in splits]

    async def delete_transaction(self, txn_id: int) -> None:
        txn = await self.session.get(Transaction, txn_id)
        if txn:
            await self.session.delete(txn)
