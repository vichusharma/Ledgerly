"""Statement import service — multi-format parsing, dedup via savepoints, auto-snapshot.

Format detection and parsing live in ``app.domains.imports.parsers``. This
service orchestrates: detect → parse to canonical RawTxns → dedup + categorize
+ insert (per-row savepoints) → refresh the net-worth snapshot.
"""
from __future__ import annotations

import datetime
from decimal import InvalidOperation
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.accounts.models import Account
from app.domains.imports import parsers
from app.domains.imports.models import ImportMapping
from app.domains.imports.parsers import csv_parser
from app.domains.imports.parsers.base import RawTxn
from app.domains.imports.schemas import (
    ColumnMappingIn,
    ImportBatchOut,
    ImportMappingOut,
    SampleTxn,
    StatementPreviewOut,
    ValuationCandidateOut,
    ValuationPreviewOut,
    ValuationSaveIn,
    ValuationSaveOut,
)
from app.domains.transactions.models import ImportBatch, Transaction
from app.domains.transactions.service import TransactionService


class ImportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Mappings ──────────────────────────────────────────────────────────

    async def list_mappings(self) -> list[ImportMappingOut]:
        result = await self.session.execute(select(ImportMapping))
        return [ImportMappingOut.model_validate(m) for m in result.scalars()]

    async def save_mapping(self, body: ColumnMappingIn) -> ImportMappingOut:
        existing = await self.session.execute(
            select(ImportMapping).where(ImportMapping.institution == body.institution)
        )
        mapping = existing.scalar_one_or_none()
        if mapping:
            mapping.column_map = body.column_map
            mapping.date_format = body.date_format
            mapping.decimal_separator = body.decimal_separator
            mapping.encoding = body.encoding
            mapping.skip_rows = body.skip_rows
        else:
            mapping = ImportMapping(
                institution=body.institution,
                column_map=body.column_map,
                date_format=body.date_format,
                decimal_separator=body.decimal_separator,
                encoding=body.encoding,
                skip_rows=body.skip_rows,
            )
            self.session.add(mapping)
        await self.session.flush()
        return ImportMappingOut.model_validate(mapping)

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _decode(content: bytes, encoding: str = "utf-8") -> str:
        for enc in (encoding, "utf-8", "latin-1"):
            try:
                return content.decode(enc)
            except (UnicodeDecodeError, LookupError):
                continue
        return content.decode("utf-8", errors="ignore")

    async def _account_institution(self, account_id: int) -> str | None:
        account = await self.session.get(Account, account_id)
        return account.institution if account else None

    # ── Preview (no DB write) ─────────────────────────────────────────────

    async def preview_statement(
        self, content: bytes, filename: str | None, account_id: int | None
    ) -> StatementPreviewOut:
        fmt = parsers.detect_format(filename, content)

        if fmt != "csv":
            txns = parsers.parse_non_csv(fmt, content)
            return StatementPreviewOut(
                format=fmt,
                sample_txns=[
                    SampleTxn(date=t.date, amount=t.amount, description=t.description)
                    for t in txns[:5]
                ],
            )

        # CSV: build the mapping preview.
        text = self._decode(content)
        headers, rows, delimiter = csv_parser.read_rows(text)
        detected = csv_parser.detect_columns(headers)

        institution = (
            await self._account_institution(account_id) if account_id else None
        )
        preset = parsers.presets.match(institution)
        preset_matched = False
        date_format = "%d/%m/%Y"
        decimal_separator = ","
        if preset:
            preset_matched = True
            date_format = preset.get("date_format", date_format)
            decimal_separator = preset.get("decimal_separator", decimal_separator)
            # Only adopt preset column names that actually exist in this file.
            for key, col in preset.get("column_map", {}).items():
                if col in headers:
                    detected[key] = col

        sample_txns = csv_parser.build_txns(rows[:5], detected, date_format, decimal_separator)
        return StatementPreviewOut(
            format="csv",
            headers=headers,
            delimiter=delimiter,
            detected=detected,
            preset_matched=preset_matched,
            sample=[dict(r) for r in rows[:3]],
            sample_txns=[
                SampleTxn(date=t.date, amount=t.amount, description=t.description)
                for t in sample_txns
            ],
        )

    # ── Import ────────────────────────────────────────────────────────────

    async def import_statement(
        self,
        content: bytes,
        filename: str,
        account_id: int,
        mapping_id: int | None = None,
        # Explicit CSV column overrides (take priority over preset/saved/auto)
        date_col: str | None = None,
        amount_col: str | None = None,
        debit_col: str | None = None,
        credit_col: str | None = None,
        desc_col: str | None = None,
        delimiter: str | None = None,
        date_format: str = "%d/%m/%Y",
        decimal_separator: str = ",",
        save_as: str | None = None,
    ) -> ImportBatchOut:
        fmt = parsers.detect_format(filename, content)

        if fmt != "csv":
            txns = parsers.parse_non_csv(fmt, content)
        else:
            txns = await self._csv_txns(
                content, account_id, mapping_id,
                date_col, amount_col, debit_col, credit_col, desc_col,
                delimiter, date_format, decimal_separator, save_as,
            )

        return await self._persist(txns, account_id, filename)

    async def _csv_txns(
        self,
        content: bytes,
        account_id: int,
        mapping_id: int | None,
        date_col: str | None,
        amount_col: str | None,
        debit_col: str | None,
        credit_col: str | None,
        desc_col: str | None,
        delimiter: str | None,
        date_format: str,
        decimal_separator: str,
        save_as: str | None,
    ) -> list[RawTxn]:
        # 1. Saved mapping (if explicitly selected)
        col_map: dict[str, Any] = {}
        skip_rows: int | None = None
        encoding = "utf-8"
        if mapping_id:
            m = await self.session.get(ImportMapping, mapping_id)
            if m:
                col_map = m.column_map or {}
                date_format = m.date_format
                decimal_separator = m.decimal_separator
                encoding = m.encoding
                skip_rows = m.skip_rows or None
                delimiter = delimiter or col_map.get("delimiter")

        # 2. Bank preset (by the account's institution)
        institution = await self._account_institution(account_id)
        preset = parsers.presets.match(institution)
        preset_cols: dict[str, str] = {}
        if preset and not mapping_id:
            date_format = date_format if date_col else preset.get("date_format", date_format)
            decimal_separator = (
                decimal_separator if amount_col or debit_col or credit_col
                else preset.get("decimal_separator", decimal_separator)
            )
            delimiter = delimiter or preset.get("delimiter")
            preset_cols = preset.get("column_map", {})

        # 3. Read rows
        text = self._decode(content, encoding)
        headers, rows, _ = csv_parser.read_rows(text, delimiter=delimiter, skip_rows=skip_rows)
        detected = csv_parser.detect_columns(headers)

        def resolve(field: str, override: str | None) -> str | None:
            # explicit override → saved mapping → preset (if in headers) → auto-detect
            if override:
                return override
            if col_map.get(field):
                return col_map[field]
            preset_col = preset_cols.get(field)
            if preset_col and preset_col in headers:
                return preset_col
            return detected.get(field)

        cols = {
            "date": resolve("date", date_col),
            "amount": resolve("amount", amount_col),
            "debit": resolve("debit", debit_col),
            "credit": resolve("credit", credit_col),
            "description": resolve("description", desc_col),
        }

        # 4. Optionally persist this mapping for future use
        if save_as:
            await self._save_resolved_mapping(
                save_as, cols, delimiter, date_format, decimal_separator
            )

        return csv_parser.build_txns(rows, cols, date_format, decimal_separator)

    async def _save_resolved_mapping(
        self, institution: str, cols: dict, delimiter: str | None,
        date_format: str, decimal_separator: str,
    ) -> None:
        new_col_map = {k: v for k, v in {**cols, "delimiter": delimiter}.items() if v}
        existing = await self.session.execute(
            select(ImportMapping).where(ImportMapping.institution == institution)
        )
        existing_m = existing.scalar_one_or_none()
        if existing_m:
            existing_m.column_map = new_col_map
            existing_m.date_format = date_format
            existing_m.decimal_separator = decimal_separator
        else:
            self.session.add(ImportMapping(
                institution=institution,
                column_map=new_col_map,
                date_format=date_format,
                decimal_separator=decimal_separator,
            ))
        await self.session.flush()

    async def _persist(
        self, txns: list[RawTxn], account_id: int, filename: str
    ) -> ImportBatchOut:
        batch = ImportBatch(
            account_id=account_id,
            filename=filename,
            imported_at=datetime.datetime.utcnow(),
            row_count=0,
            duplicate_count=0,
        )
        self.session.add(batch)
        await self.session.flush()

        txn_service = TransactionService(self.session)
        rules = await txn_service._get_rules()
        label_rules = await txn_service._get_label_rules()
        imported = 0
        dupes = 0

        for raw in txns:
            try:
                dedup_hash = Transaction.compute_hash(
                    account_id, raw.date, raw.amount, raw.description
                )
                category_id = txn_service._auto_categorize(raw.description, rules)
                label_ids = txn_service._auto_label(raw.description, label_rules)
                txn = Transaction(
                    account_id=account_id,
                    import_batch_id=batch.id,
                    date=raw.date,
                    amount=raw.amount,
                    description=raw.description,
                    category_id=category_id,
                    dedup_hash=dedup_hash,
                )
                if label_ids:
                    txn.labels = txn_service._labels_from_rules(label_ids, label_rules)
                # Savepoint per row so a duplicate doesn't roll back the whole session.
                async with self.session.begin_nested():
                    self.session.add(txn)
                    await self.session.flush()
                imported += 1
            except IntegrityError:
                dupes += 1
            except (InvalidOperation, ValueError, KeyError):
                continue

        batch.row_count = imported
        batch.duplicate_count = dupes
        await self.session.flush()

        # Refresh today's net-worth snapshot so the dashboard reflects new transactions.
        from app.domains.networth.service import NetWorthService
        await NetWorthService(self.session).take_snapshot()

        return ImportBatchOut.model_validate(batch)

    # ── Batch management ──────────────────────────────────────────────────

    async def list_batches(self) -> list[ImportBatchOut]:
        result = await self.session.execute(
            select(ImportBatch).order_by(ImportBatch.imported_at.desc())
        )
        return [ImportBatchOut.model_validate(b) for b in result.scalars()]

    async def rollback_batch(self, batch_id: int) -> bool:
        batch = await self.session.get(ImportBatch, batch_id)
        if batch is None or batch.is_rolled_back:
            return False
        txns = await self.session.execute(
            select(Transaction).where(Transaction.import_batch_id == batch_id)
        )
        for txn in txns.scalars():
            await self.session.delete(txn)
        batch.is_rolled_back = True
        await self.session.flush()
        return True

    # ── Wrapper valuation statements (AV annual relevés etc.) ─────────────

    async def preview_valuation(self, content: bytes) -> ValuationPreviewOut:
        """Extract candidate fund valuations from a statement PDF. No DB write."""
        from app.domains.imports.parsers.pdf_valuation_parser import parse_pdf_valuation

        preview = parse_pdf_valuation(content)
        return ValuationPreviewOut(
            as_of_date=(
                datetime.date.fromisoformat(preview.as_of_date)
                if preview.as_of_date else None
            ),
            candidates=[
                ValuationCandidateOut(label=c.label, value=c.value)
                for c in preview.candidates
            ],
        )

    async def save_valuation(self, body: ValuationSaveIn) -> ValuationSaveOut:
        """Persist reviewed fund valuations as ``valuation`` lots.

        Per item: resolve the Instrument (by id, else case-insensitive name
        match, else create one), then upsert an InvestmentLot with
        lot_type=valuation, quantity=1, price=value for (account, instrument,
        as_of_date) — re-submitting a corrected review updates in place.
        """
        from decimal import Decimal

        from app.domains.investments.models import (
            AssetClass,
            Instrument,
            InvestmentLot,
            LotType,
        )

        account = await self.session.get(Account, body.account_id)
        currency = account.currency if account else "EUR"

        saved = 0
        created_instruments = 0
        total = Decimal("0")

        for item in body.items:
            inst = None
            if item.instrument_id:
                inst = await self.session.get(Instrument, item.instrument_id)
            if inst is None:
                result = await self.session.execute(
                    select(Instrument).where(
                        func.lower(Instrument.name) == item.label.strip().lower()
                    )
                )
                inst = result.scalars().first()
            if inst is None:
                inst = Instrument(
                    name=item.label.strip(),
                    asset_class=AssetClass.other,
                    currency=currency,
                )
                self.session.add(inst)
                await self.session.flush()
                created_instruments += 1

            existing = await self.session.execute(
                select(InvestmentLot).where(
                    InvestmentLot.account_id == body.account_id,
                    InvestmentLot.instrument_id == inst.id,
                    InvestmentLot.lot_type == LotType.valuation,
                    InvestmentLot.settled_at == body.as_of_date,
                )
            )
            lot = existing.scalars().first()
            if lot:
                lot.quantity = Decimal("1")
                lot.price = item.value
            else:
                self.session.add(InvestmentLot(
                    account_id=body.account_id,
                    instrument_id=inst.id,
                    lot_type=LotType.valuation,
                    quantity=Decimal("1"),
                    price=item.value,
                    currency=currency,
                    settled_at=body.as_of_date,
                    notes="Imported from valuation statement",
                ))
            saved += 1
            total += item.value

        await self.session.flush()

        # Refresh today's net-worth snapshot so the dashboard reflects the new values.
        from app.domains.networth.service import NetWorthService
        await NetWorthService(self.session).take_snapshot()

        return ValuationSaveOut(
            saved=saved, created_instruments=created_instruments, total_value=total
        )
