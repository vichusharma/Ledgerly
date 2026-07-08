"""Tax filing service — Features J1-J6 (docs/Backlog.md): per-person
residency profile + seeded treaty metadata lookup, RSU/ESPP/foreign-
income/foreign-account ingestion, encrypted document storage,
`FilingSnapshot` compute/validate, and Cerfa-facsimile PDF generation.
Mirrors `TaxService`'s shape (direct session queries, no repository
split)."""
from __future__ import annotations

import dataclasses
import datetime
import io
import json
import zipfile
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tax_filing_rules import (
    map_estimate_to_2042_boxes,
    map_foreign_accounts_to_3916_entries,
    map_foreign_income_to_2047_lines,
    map_investment_income_to_2042_boxes,
    validate_filing_inputs,
)
from app.domains.accounts.models import Person
from app.domains.investments.models import InvestmentLot, LotType, VestingSchedule
from app.domains.tax.service import TaxService
from app.domains.tax_filing.models import (
    FilingSnapshot,
    ForeignAccountDeclaration,
    ForeignIncomeDeclaration,
    PersonTaxResidency,
    TaxDocument,
    TaxDocumentType,
    TreatyMetadata,
)
from app.domains.tax_filing.parsers.espp_purchase_parser import parse_pdf_espp_purchase
from app.domains.tax_filing.parsers.foreign_bank_statement_parser import (
    parse_pdf_foreign_bank_statement,
)
from app.domains.tax_filing.parsers.foreign_dividend_statement_parser import (
    parse_pdf_foreign_dividend_statement,
)
from app.domains.tax_filing.parsers.rsu_vesting_parser import parse_pdf_rsu_vesting
from app.domains.tax_filing.pdf.generator import (
    generate_2042_pdf,
    generate_2047_pdf,
    generate_3916_pdf,
)
from app.domains.tax_filing.schemas import (
    EsppPurchaseConfirmIn,
    EsppPurchaseOut,
    EsppPurchasePreviewOut,
    FilingSnapshotOut,
    FilingSnapshotPayload,
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
from app.infra.document_crypto import decrypt_bytes, encrypt_bytes

# In-code fallback mirroring migration 0013_treaty_metadata.py's seed —
# needed because the integration-test DB fixture builds tables via
# `Base.metadata.create_all()` directly and never runs Alembic
# migrations, so the migration's `op.bulk_insert` seed never lands there
# (same gotcha as TaxService._get_tax_year_config's fallback).
_DEFAULT_TREATIES = [
    TreatyMetadataOut(
        country_code="IN", country_name="India",
        default_elimination_method="credit_equal_to_french_tax",
        treaty_reference="Convention France-Inde du 29/09/1992", notes=None,
    ),
    TreatyMetadataOut(
        country_code="US", country_name="United States",
        default_elimination_method="credit_equal_to_french_tax",
        treaty_reference="Convention France-Etats-Unis du 31/08/1994", notes=None,
    ),
    TreatyMetadataOut(
        country_code="GB", country_name="United Kingdom",
        default_elimination_method="credit_equal_to_french_tax",
        treaty_reference="Convention France-Royaume-Uni du 19/06/2008", notes=None,
    ),
    TreatyMetadataOut(
        country_code="CA", country_name="Canada",
        default_elimination_method="credit_equal_to_french_tax",
        treaty_reference="Convention France-Canada du 02/05/1975", notes=None,
    ),
    TreatyMetadataOut(
        country_code="DE", country_name="Germany",
        default_elimination_method="exemption_with_effective_rate",
        treaty_reference="Convention France-Allemagne du 21/07/1959", notes=None,
    ),
]


class TaxFilingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _get_residency_row(self, person_id: int) -> PersonTaxResidency | None:
        result = await self.session.execute(
            select(PersonTaxResidency).where(PersonTaxResidency.person_id == person_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _to_out(person_id: int, row: PersonTaxResidency | None) -> PersonTaxResidencyOut:
        if row is None:
            return PersonTaxResidencyOut(
                person_id=person_id,
                home_country_code=None,
                home_country_tax_id=None,
                french_tax_number=None,
                notes=None,
            )
        return PersonTaxResidencyOut(
            person_id=person_id,
            home_country_code=row.home_country_code,
            home_country_tax_id=row.home_country_tax_id,
            french_tax_number=row.french_tax_number,
            notes=row.notes,
        )

    async def get_person_residency(self, person_id: int) -> PersonTaxResidencyOut | None:
        person = await self.session.get(Person, person_id)
        if person is None:
            return None
        row = await self._get_residency_row(person_id)
        return self._to_out(person_id, row)

    async def set_person_residency(
        self, person_id: int, body: PersonTaxResidencyUpdateIn
    ) -> PersonTaxResidencyOut | None:
        person = await self.session.get(Person, person_id)
        if person is None:
            return None
        row = await self._get_residency_row(person_id)
        if row is None:
            row = PersonTaxResidency(person_id=person_id)
            self.session.add(row)
        row.home_country_code = body.home_country_code
        row.home_country_tax_id = body.home_country_tax_id
        row.french_tax_number = body.french_tax_number
        row.notes = body.notes
        await self.session.flush()
        return self._to_out(person_id, row)

    async def list_treaties(self) -> list[TreatyMetadataOut]:
        result = await self.session.execute(
            select(TreatyMetadata).order_by(TreatyMetadata.country_name)
        )
        rows = [TreatyMetadataOut.model_validate(row) for row in result.scalars()]
        if not rows:
            # Table has zero rows (migrations not yet run, e.g. the
            # integration-test DB fixture) — degrade to the same in-code
            # default rather than returning an empty, unusable list.
            return list(_DEFAULT_TREATIES)
        return rows

    # -- Feature J3: encrypted document storage --------------------------

    async def store_document(
        self,
        content: bytes,
        *,
        original_filename: str,
        content_type: str,
        document_type: TaxDocumentType,
        person_id: int | None = None,
        tax_year: int | None = None,
        related_record_type: str | None = None,
        related_record_id: int | None = None,
    ) -> TaxDocumentOut:
        row = TaxDocument(
            person_id=person_id,
            tax_year=tax_year,
            document_type=document_type,
            original_filename=original_filename,
            content_type=content_type,
            encrypted_content=encrypt_bytes(content),
            related_record_type=related_record_type,
            related_record_id=related_record_id,
        )
        self.session.add(row)
        await self.session.flush()
        return TaxDocumentOut.model_validate(row)

    async def list_documents(
        self, person_id: int | None = None, tax_year: int | None = None
    ) -> list[TaxDocumentOut]:
        query = select(TaxDocument).order_by(TaxDocument.uploaded_at.desc())
        if person_id is not None:
            query = query.where(TaxDocument.person_id == person_id)
        if tax_year is not None:
            query = query.where(TaxDocument.tax_year == tax_year)
        result = await self.session.execute(query)
        return [TaxDocumentOut.model_validate(row) for row in result.scalars()]

    async def get_document_content(
        self, document_id: int
    ) -> tuple[TaxDocumentOut, bytes] | None:
        row = await self.session.get(TaxDocument, document_id)
        if row is None:
            return None
        return TaxDocumentOut.model_validate(row), decrypt_bytes(row.encrypted_content)

    async def delete_document(self, document_id: int) -> bool:
        row = await self.session.get(TaxDocument, document_id)
        if row is None:
            return False
        await self.session.delete(row)
        await self.session.flush()
        return True

    # -- Feature J2: RSU vesting -------------------------------------------

    def preview_rsu_vesting(self, content: bytes) -> RsuVestingPreviewOut:
        return parse_pdf_rsu_vesting(content)

    async def confirm_rsu_vesting(
        self,
        content: bytes,
        *,
        original_filename: str,
        content_type: str,
        body: RsuVestingConfirmIn,
    ) -> RsuVestingOut:
        # Upsert by the natural key (account, instrument, grant date) —
        # re-confirming a vest event for the same grant updates the
        # schedule's static facts rather than duplicating it.
        result = await self.session.execute(
            select(VestingSchedule).where(
                VestingSchedule.account_id == body.account_id,
                VestingSchedule.instrument_id == body.instrument_id,
                VestingSchedule.grant_date == body.grant_date,
            )
        )
        schedule = result.scalar_one_or_none()
        if schedule is None:
            schedule = VestingSchedule(
                account_id=body.account_id,
                instrument_id=body.instrument_id,
                grant_date=body.grant_date,
                total_shares=body.total_shares,
                cliff_months=body.cliff_months,
                vesting_months=body.vesting_months,
                grant_price=body.grant_price,
            )
            self.session.add(schedule)
        else:
            schedule.total_shares = body.total_shares
            schedule.cliff_months = body.cliff_months
            schedule.vesting_months = body.vesting_months
            schedule.grant_price = body.grant_price
        await self.session.flush()

        lot = InvestmentLot(
            account_id=body.account_id,
            instrument_id=body.instrument_id,
            lot_type=LotType.vesting,
            quantity=body.vested_shares,
            price=body.vest_fmv,
            settled_at=body.vest_date,
            vesting_schedule_id=schedule.id,
        )
        self.session.add(lot)
        await self.session.flush()

        await self.store_document(
            content,
            original_filename=original_filename,
            content_type=content_type,
            document_type=TaxDocumentType.rsu_vesting,
            person_id=body.person_id,
            tax_year=body.tax_year,
            related_record_type="investment_lot",
            related_record_id=lot.id,
        )

        return RsuVestingOut(
            vesting_schedule_id=schedule.id,
            lot_id=lot.id,
            account_id=body.account_id,
            instrument_id=body.instrument_id,
            grant_date=schedule.grant_date,
            total_shares=schedule.total_shares,
            cliff_months=schedule.cliff_months,
            vesting_months=schedule.vesting_months,
            grant_price=schedule.grant_price,
            vest_date=lot.settled_at,
            vested_shares=lot.quantity,
            vest_fmv=lot.price,
        )

    # -- Feature J2: ESPP purchases -----------------------------------------

    def preview_espp_purchase(self, content: bytes) -> EsppPurchasePreviewOut:
        return parse_pdf_espp_purchase(content)

    async def confirm_espp_purchase(
        self,
        content: bytes,
        *,
        original_filename: str,
        content_type: str,
        body: EsppPurchaseConfirmIn,
    ) -> EsppPurchaseOut:
        lot = InvestmentLot(
            account_id=body.account_id,
            instrument_id=body.instrument_id,
            lot_type=LotType.buy,
            quantity=body.shares,
            price=body.purchase_price,
            settled_at=body.purchase_date,
            fmv_at_acquisition=body.fmv_at_purchase,
            discount_pct=body.discount_pct,
        )
        self.session.add(lot)
        await self.session.flush()

        await self.store_document(
            content,
            original_filename=original_filename,
            content_type=content_type,
            document_type=TaxDocumentType.espp_purchase,
            person_id=body.person_id,
            tax_year=body.tax_year,
            related_record_type="investment_lot",
            related_record_id=lot.id,
        )

        return EsppPurchaseOut(
            lot_id=lot.id,
            account_id=body.account_id,
            instrument_id=body.instrument_id,
            purchase_date=lot.settled_at,
            shares=lot.quantity,
            purchase_price=lot.price,
            fmv_at_acquisition=lot.fmv_at_acquisition,
            discount_pct=lot.discount_pct,
        )

    # -- Feature J2: foreign income (Form 2047) -----------------------------

    def preview_foreign_income(self, content: bytes) -> ForeignIncomePreviewOut:
        return parse_pdf_foreign_dividend_statement(content)

    async def create_foreign_income(
        self, body: ForeignIncomeCreateIn
    ) -> ForeignIncomeOut:
        row = ForeignIncomeDeclaration(
            person_id=body.person_id,
            tax_year=body.tax_year,
            income_type=body.income_type,
            source_country_code=body.source_country_code,
            source_description=body.source_description,
            gross_amount_eur=body.gross_amount_eur,
            foreign_tax_paid_eur=body.foreign_tax_paid_eur,
            elimination_method_override=body.elimination_method_override,
            notes=body.notes,
        )
        self.session.add(row)
        await self.session.flush()
        return ForeignIncomeOut.model_validate(row)

    async def confirm_foreign_income(
        self,
        content: bytes,
        *,
        original_filename: str,
        content_type: str,
        body: ForeignIncomeCreateIn,
    ) -> ForeignIncomeOut:
        out = await self.create_foreign_income(body)
        await self.store_document(
            content,
            original_filename=original_filename,
            content_type=content_type,
            document_type=TaxDocumentType.foreign_dividend,
            person_id=body.person_id,
            tax_year=body.tax_year,
            related_record_type="foreign_income_declaration",
            related_record_id=out.id,
        )
        return out

    async def list_foreign_income(
        self, person_id: int | None = None, tax_year: int | None = None
    ) -> list[ForeignIncomeOut]:
        query = select(ForeignIncomeDeclaration).order_by(
            ForeignIncomeDeclaration.tax_year.desc(), ForeignIncomeDeclaration.id
        )
        if person_id is not None:
            query = query.where(ForeignIncomeDeclaration.person_id == person_id)
        if tax_year is not None:
            query = query.where(ForeignIncomeDeclaration.tax_year == tax_year)
        result = await self.session.execute(query)
        return [ForeignIncomeOut.model_validate(row) for row in result.scalars()]

    async def update_foreign_income(
        self, declaration_id: int, body: ForeignIncomeUpdateIn
    ) -> ForeignIncomeOut | None:
        row = await self.session.get(ForeignIncomeDeclaration, declaration_id)
        if row is None:
            return None
        for key, value in body.model_dump(exclude_unset=True).items():
            setattr(row, key, value)
        await self.session.flush()
        return ForeignIncomeOut.model_validate(row)

    async def delete_foreign_income(self, declaration_id: int) -> bool:
        row = await self.session.get(ForeignIncomeDeclaration, declaration_id)
        if row is None:
            return False
        await self.session.delete(row)
        await self.session.flush()
        return True

    # -- Feature J2: foreign accounts (Form 3916) ---------------------------

    def preview_foreign_account(self, content: bytes) -> ForeignAccountPreviewOut:
        return parse_pdf_foreign_bank_statement(content)

    async def create_foreign_account(
        self, body: ForeignAccountCreateIn
    ) -> ForeignAccountOut:
        row = ForeignAccountDeclaration(
            person_id=body.person_id,
            tax_year=body.tax_year,
            account_id=body.account_id,
            bank_name=body.bank_name,
            country_code=body.country_code,
            account_identifier_masked=body.account_identifier_masked,
            opened_this_year=body.opened_this_year,
            closed_this_year=body.closed_this_year,
            notes=body.notes,
        )
        self.session.add(row)
        await self.session.flush()
        return ForeignAccountOut.model_validate(row)

    async def confirm_foreign_account(
        self,
        content: bytes,
        *,
        original_filename: str,
        content_type: str,
        body: ForeignAccountCreateIn,
    ) -> ForeignAccountOut:
        out = await self.create_foreign_account(body)
        await self.store_document(
            content,
            original_filename=original_filename,
            content_type=content_type,
            document_type=TaxDocumentType.foreign_bank_statement,
            person_id=body.person_id,
            tax_year=body.tax_year,
            related_record_type="foreign_account_declaration",
            related_record_id=out.id,
        )
        return out

    async def list_foreign_accounts(
        self, person_id: int | None = None, tax_year: int | None = None
    ) -> list[ForeignAccountOut]:
        query = select(ForeignAccountDeclaration).order_by(
            ForeignAccountDeclaration.tax_year.desc(), ForeignAccountDeclaration.id
        )
        if person_id is not None:
            query = query.where(ForeignAccountDeclaration.person_id == person_id)
        if tax_year is not None:
            query = query.where(ForeignAccountDeclaration.tax_year == tax_year)
        result = await self.session.execute(query)
        return [ForeignAccountOut.model_validate(row) for row in result.scalars()]

    async def update_foreign_account(
        self, declaration_id: int, body: ForeignAccountUpdateIn
    ) -> ForeignAccountOut | None:
        row = await self.session.get(ForeignAccountDeclaration, declaration_id)
        if row is None:
            return None
        for key, value in body.model_dump(exclude_unset=True).items():
            setattr(row, key, value)
        await self.session.flush()
        return ForeignAccountOut.model_validate(row)

    async def delete_foreign_account(self, declaration_id: int) -> bool:
        row = await self.session.get(ForeignAccountDeclaration, declaration_id)
        if row is None:
            return False
        await self.session.delete(row)
        await self.session.flush()
        return True

    # -- Feature J5: FilingSnapshot compute/validate ------------------------

    async def _build_filing_payload(self, year: int) -> FilingSnapshotPayload:
        tax_service = TaxService(self.session)
        estimate = await tax_service.get_tax_estimate(year, include_investments=True)
        brackets, plafond = await tax_service.get_bareme_config(year)

        parts = estimate.parts if estimate.parts is not None else Decimal("1")
        base_parts = Decimal("2") if estimate.filing_status == "married_pacs" else Decimal("1")

        foreign_income = await self.list_foreign_income(tax_year=year)
        foreign_accounts = await self.list_foreign_accounts(tax_year=year)
        treaties = await self.list_treaties()
        treaty_defaults = {t.country_code: t.default_elimination_method.value for t in treaties}

        lines_2047 = map_foreign_income_to_2047_lines(
            [d.model_dump() for d in foreign_income], treaty_defaults,
            estimate.household_taxable_income_projected, parts, base_parts,
            brackets, plafond,
        )
        entries_3916 = map_foreign_accounts_to_3916_entries(
            [d.model_dump() for d in foreign_accounts]
        )

        salaries = [p.gross_annual_projected for p in estimate.persons]
        dividends = (
            estimate.investment_income.dividends_total
            if estimate.investment_income else Decimal("0")
        )
        pfu_chosen = bool(
            estimate.investment_income and estimate.investment_income.chosen_method == "pfu"
        )
        boxes_2042 = (
            map_estimate_to_2042_boxes(salaries)
            + map_investment_income_to_2042_boxes(dividends, pfu_chosen)
        )

        # -- Validation inputs --
        residencies = (await self.session.execute(select(PersonTaxResidency))).scalars()
        has_residency = any(r.home_country_code for r in residencies)

        docs_result = await self.session.execute(
            select(TaxDocument.related_record_type, TaxDocument.related_record_id)
            .where(TaxDocument.tax_year == year)
        )
        covered = {(t, i) for t, i in docs_result if i is not None}
        missing_docs = [
            f"foreign_income_{d.id}" for d in foreign_income
            if ("foreign_income_declaration", d.id) not in covered
        ] + [
            f"foreign_account_{d.id}" for d in foreign_accounts
            if ("foreign_account_declaration", d.id) not in covered
        ]
        validation_issues = validate_filing_inputs(
            has_residency=has_residency,
            foreign_income_countries={d.source_country_code for d in foreign_income},
            declared_foreign_account_countries={d.country_code for d in foreign_accounts},
            declarations_missing_documents=missing_docs,
        )

        simplifications = list(estimate.simplifications_applied) + [
            "cerfa_box_codes_unverified",
            "treaty_metadata_seeded_handful_of_countries",
        ]
        if any("treaty_method_defaulted_unseeded_country" in line.simplification_keys
               for line in lines_2047):
            simplifications.append("treaty_method_defaulted_unseeded_country")

        return FilingSnapshotPayload(
            year=year,
            bareme_tax_year_used=estimate.bareme_tax_year_used,
            estimated_tax=estimate.estimated_tax,
            balance=estimate.balance,
            boxes_2042=[dataclasses.asdict(b) for b in boxes_2042],
            lines_2047=[dataclasses.asdict(line) for line in lines_2047],
            entries_3916=[dataclasses.asdict(e) for e in entries_3916],
            validation_issues=validation_issues,
            simplifications_applied=simplifications,
        )

    async def compute_filing(self, year: int) -> FilingSnapshotOut:
        """Upserts a `FilingSnapshot` for `year`. Raises `ValueError` if
        an existing snapshot for that year is locked (router converts
        this to a 409)."""
        result = await self.session.execute(
            select(FilingSnapshot).where(FilingSnapshot.tax_year == year)
        )
        row = result.scalar_one_or_none()
        if row is not None and row.locked:
            raise ValueError(f"Filing snapshot for {year} is locked — unlock it first")

        payload = await self._build_filing_payload(year)
        payload_dict = json.loads(payload.model_dump_json())
        if row is None:
            row = FilingSnapshot(tax_year=year, payload=payload_dict)
            self.session.add(row)
        else:
            row.payload = payload_dict
        await self.session.flush()
        # `computed_at` uses onupdate=func.now() — on an UPDATE (not the
        # first INSERT) SQLAlchemy expires it rather than refetching, so
        # a synchronous pydantic read right after flush() would try a
        # lazy load outside the async context (MissingGreenlet).
        await self.session.refresh(row)
        return FilingSnapshotOut.model_validate(row)

    async def get_filing(self, year: int) -> FilingSnapshotOut | None:
        result = await self.session.execute(
            select(FilingSnapshot).where(FilingSnapshot.tax_year == year)
        )
        row = result.scalar_one_or_none()
        return FilingSnapshotOut.model_validate(row) if row else None

    async def validate_filing(self, year: int) -> list[str]:
        """Runs validation fresh, independent of any stored snapshot."""
        payload = await self._build_filing_payload(year)
        return payload.validation_issues

    async def lock_filing(self, year: int) -> FilingSnapshotOut | None:
        result = await self.session.execute(
            select(FilingSnapshot).where(FilingSnapshot.tax_year == year)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.locked = True
        row.locked_at = datetime.datetime.now(datetime.UTC)
        await self.session.flush()
        await self.session.refresh(row)
        return FilingSnapshotOut.model_validate(row)

    async def unlock_filing(self, year: int) -> FilingSnapshotOut | None:
        result = await self.session.execute(
            select(FilingSnapshot).where(FilingSnapshot.tax_year == year)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.locked = False
        row.locked_at = None
        await self.session.flush()
        await self.session.refresh(row)
        return FilingSnapshotOut.model_validate(row)

    # -- Feature J6: Cerfa-facsimile PDF generation --------------------------

    _PDF_GENERATORS = {
        "2042": generate_2042_pdf,
        "2047": generate_2047_pdf,
        "3916": generate_3916_pdf,
    }

    async def generate_pdf(self, year: int, form: str) -> bytes | None:
        """`form` in {"2042", "2047", "3916", "all"} ("all" returns a zip
        bundle of all three). Reads the existing `FilingSnapshot` for
        `year` — returns None if none has been computed yet (caller
        4-oh-fours). Does not compute or lock as a side effect; the
        router optionally locks afterward via a `lock` query param.
        """
        snapshot = await self.get_filing(year)
        if snapshot is None:
            return None
        payload = snapshot.payload

        if form in self._PDF_GENERATORS:
            return self._PDF_GENERATORS[form](payload)

        if form == "all":
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for name, generator in self._PDF_GENERATORS.items():
                    zf.writestr(f"{name}_{year}.pdf", generator(payload))
            return buf.getvalue()

        raise ValueError(f"Unknown form '{form}' — expected 2042, 2047, 3916, or all")
