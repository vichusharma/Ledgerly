"""Salary domain service — payslip preview/confirm, list, delete.

Mirrors ImportService's wrapper-valuation flow: preview does no DB
write, confirm upserts by the (person_id, pay_period) natural key so a
re-uploaded/corrected month replaces rather than duplicates.
"""
from __future__ import annotations

import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.salary.models import Payslip
from app.domains.salary.schemas import PayslipConfirmIn, PayslipOut, PayslipPreviewOut


class SalaryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def preview_payslip(self, content: bytes) -> PayslipPreviewOut:
        """Extract candidate fields from a payslip PDF. No DB write."""
        from app.domains.salary.parsers.pdf_payslip_parser import parse_pdf_payslip

        preview = parse_pdf_payslip(content)
        return PayslipPreviewOut(
            pay_period=preview.pay_period,
            employer=preview.employer,
            gross=preview.gross,
            net_taxable=preview.net_taxable,
            net_before_tax=preview.net_before_tax,
            net_paid=preview.net_paid,
            pas_rate=preview.pas_rate,
            pas_withheld=preview.pas_withheld,
            ytd_gross=preview.ytd_gross,
            ytd_net_taxable=preview.ytd_net_taxable,
            ytd_pas_withheld=preview.ytd_pas_withheld,
        )

    async def save_payslip(self, body: PayslipConfirmIn) -> PayslipOut:
        """Upsert the reviewed payslip by (person_id, pay_period)."""
        existing = await self.session.execute(
            select(Payslip).where(
                Payslip.person_id == body.person_id,
                Payslip.pay_period == body.pay_period,
            )
        )
        payslip = existing.scalar_one_or_none()
        fields = body.model_dump(exclude={"person_id", "pay_period"})
        if payslip:
            for key, value in fields.items():
                setattr(payslip, key, value)
        else:
            payslip = Payslip(person_id=body.person_id, pay_period=body.pay_period, **fields)
            self.session.add(payslip)
        await self.session.flush()
        return PayslipOut.model_validate(payslip)

    async def list_payslips(
        self, person_id: int | None = None, year: int | None = None
    ) -> list[PayslipOut]:
        query = select(Payslip)
        if person_id is not None:
            query = query.where(Payslip.person_id == person_id)
        if year is not None:
            query = query.where(
                Payslip.pay_period >= datetime.date(year, 1, 1),
                Payslip.pay_period <= datetime.date(year, 12, 31),
            )
        result = await self.session.execute(query.order_by(Payslip.pay_period.desc()))
        return [PayslipOut.model_validate(p) for p in result.scalars()]

    async def delete_payslip(self, payslip_id: int) -> bool:
        payslip = await self.session.get(Payslip, payslip_id)
        if payslip is None:
            return False
        await self.session.delete(payslip)
        await self.session.flush()
        return True
