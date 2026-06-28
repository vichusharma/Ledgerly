"""CSV import service — parse, dedup, auto-categorize, persist."""
from __future__ import annotations

import csv
import datetime
import io
from decimal import Decimal, InvalidOperation

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.imports.models import ImportMapping
from app.domains.imports.schemas import ColumnMappingIn, ImportBatchOut, ImportMappingOut
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

    # ── CSV import ────────────────────────────────────────────────────────

    async def import_csv(
        self,
        content: bytes,
        filename: str,
        account_id: int,
        mapping_id: int | None = None,
    ) -> ImportBatchOut:
        # Load column mapping if provided
        col_map: dict[str, str] = {}
        date_fmt = "%d/%m/%Y"
        dec_sep = ","
        encoding = "utf-8"
        skip_rows = 0

        if mapping_id:
            m = await self.session.get(ImportMapping, mapping_id)
            if m:
                col_map = m.column_map
                date_fmt = m.date_format
                dec_sep = m.decimal_separator
                encoding = m.encoding
                skip_rows = m.skip_rows

        # Decode
        try:
            text = content.decode(encoding)
        except UnicodeDecodeError:
            text = content.decode("latin-1")

        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        rows = rows[skip_rows:]  # skip header rows

        # Build batch
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

        imported = 0
        dupes = 0

        for row in rows:
            try:
                date_raw = row.get(col_map.get("date", "date"), "").strip()
                amount_raw = row.get(col_map.get("amount", "amount"), "0").strip()
                desc_raw = row.get(col_map.get("description", "description"), "").strip()

                if not date_raw:
                    continue

                txn_date = datetime.date.fromisoformat(date_raw) if "-" in date_raw else \
                    datetime.datetime.strptime(date_raw, date_fmt).date()

                # Normalise decimal separator
                amount_str = amount_raw.replace(dec_sep, ".").replace(" ", "").replace(" ", "")
                amount = Decimal(amount_str)
                dedup_hash = Transaction.compute_hash(account_id, txn_date, amount, desc_raw)

                category_id = txn_service._auto_categorize(desc_raw, rules)

                txn = Transaction(
                    account_id=account_id,
                    import_batch_id=batch.id,
                    date=txn_date,
                    amount=amount,
                    description=desc_raw,
                    category_id=category_id,
                    dedup_hash=dedup_hash,
                )
                self.session.add(txn)
                try:
                    await self.session.flush()
                    imported += 1
                except IntegrityError:
                    await self.session.rollback()
                    # Re-attach batch after rollback
                    self.session.add(batch)
                    dupes += 1

            except (InvalidOperation, ValueError, KeyError):
                continue  # Skip malformed rows

        batch.row_count = imported
        batch.duplicate_count = dupes
        await self.session.flush()
        return ImportBatchOut.model_validate(batch)

    # ── Batch management ──────────────────────────────────────────────────

    async def list_batches(self) -> list[ImportBatchOut]:
        result = await self.session.execute(
            select(ImportBatch).order_by(ImportBatch.imported_at.desc())
        )
        return [ImportBatchOut.model_validate(b) for b in result.scalars()]

    async def rollback_batch(self, batch_id: int) -> bool:
        """P2: delete all transactions in a batch and mark it rolled back."""
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
