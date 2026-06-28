"""Investments service — instruments, lots, prices, TWR/XIRR, allocation."""
from __future__ import annotations

import csv
import datetime
import io
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.allocation import compute_allocation
from app.core.performance import CashFlow, SubPeriod, twr, xirr
from app.domains.investments.models import (
    AssetClass, Instrument, InstrumentPrice, InvestmentLot, LotType,
    TargetAllocation, VestingSchedule,
)
from app.domains.investments.schemas import (
    AllocationOut, AllocationSliceOut, InstrumentCreateIn, InstrumentOut,
    LotCreateIn, LotOut, PerformanceOut, PerformanceSeriesPoint,
    PriceCreateIn, PriceOut, TargetAllocationIn,
)


class InvestmentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Instruments ───────────────────────────────────────────────────────

    async def list_instruments(self) -> list[InstrumentOut]:
        result = await self.session.execute(select(Instrument).order_by(Instrument.name))
        return [InstrumentOut.model_validate(i) for i in result.scalars()]

    async def get_instrument(self, instrument_id: int) -> InstrumentOut | None:
        i = await self.session.get(Instrument, instrument_id)
        return InstrumentOut.model_validate(i) if i else None

    async def create_instrument(self, body: InstrumentCreateIn) -> InstrumentOut:
        inst = Instrument(**body.model_dump())
        self.session.add(inst)
        await self.session.flush()
        return InstrumentOut.model_validate(inst)

    # ── Lots ──────────────────────────────────────────────────────────────

    async def list_lots(self, account_id: int | None = None) -> list[LotOut]:
        stmt = select(InvestmentLot).order_by(InvestmentLot.settled_at)
        if account_id:
            stmt = stmt.where(InvestmentLot.account_id == account_id)
        result = await self.session.execute(stmt)
        return [LotOut.model_validate(l) for l in result.scalars()]

    async def create_lot(self, body: LotCreateIn) -> LotOut:
        lot = InvestmentLot(**body.model_dump())
        self.session.add(lot)
        await self.session.flush()
        return LotOut.model_validate(lot)

    async def delete_lot(self, lot_id: int) -> None:
        lot = await self.session.get(InvestmentLot, lot_id)
        if lot:
            await self.session.delete(lot)

    # ── Prices ────────────────────────────────────────────────────────────

    async def create_price(self, body: PriceCreateIn) -> PriceOut:
        price = InstrumentPrice(**body.model_dump())
        self.session.add(price)
        try:
            await self.session.flush()
        except IntegrityError:
            await self.session.rollback()
            # Upsert: update existing
            existing = await self.session.execute(
                select(InstrumentPrice).where(
                    InstrumentPrice.instrument_id == body.instrument_id,
                    InstrumentPrice.date == body.date,
                )
            )
            p = existing.scalar_one()
            p.close = body.close
            p.currency = body.currency
            await self.session.flush()
            return PriceOut.model_validate(p)
        return PriceOut.model_validate(price)

    async def import_prices_csv(self, content: bytes) -> int:
        """Import EOD prices from CSV: columns isin,date,close[,currency]."""
        text = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        count = 0
        for row in reader:
            isin = row.get("isin", "").strip()
            date_str = row.get("date", "").strip()
            close_str = row.get("close", "0").strip()
            currency = row.get("currency", "EUR").strip()

            if not isin or not date_str:
                continue

            # Find instrument by ISIN
            result = await self.session.execute(
                select(Instrument).where(Instrument.isin == isin)
            )
            inst = result.scalar_one_or_none()
            if inst is None:
                continue

            try:
                price_date = datetime.date.fromisoformat(date_str)
                close = Decimal(close_str)
            except (ValueError, Exception):
                continue

            await self.create_price(
                PriceCreateIn(
                    instrument_id=inst.id,
                    date=price_date,
                    close=close,
                    currency=currency,
                )
            )
            count += 1
        return count

    # ── Performance (TWR + XIRR) ──────────────────────────────────────────

    async def get_performance(
        self,
        scope: str = "household",
        wrapper: str | None = None,
    ) -> PerformanceOut:
        """
        Compute TWR and XIRR for the portfolio.

        This builds sub-periods from the lot cashflows + price history.
        For each instrument: build a cashflow list (buys as negative, sells as positive,
        current value as final positive cashflow).
        """
        # Fetch lots
        stmt = select(InvestmentLot).order_by(InvestmentLot.settled_at)
        if wrapper:
            # join accounts to filter by wrapper_type
            from app.domains.accounts.models import Account
            stmt = stmt.join(Account, InvestmentLot.account_id == Account.id).where(
                Account.wrapper_type == wrapper
            )
        lots_result = await self.session.execute(stmt)
        lots = list(lots_result.scalars())

        if not lots:
            return PerformanceOut(
                twr=None, xirr=None,
                total_invested=Decimal("0"), current_value=Decimal("0"),
                total_gain=Decimal("0"), gain_pct=0.0, series=[],
            )

        today = datetime.date.today()
        total_invested = Decimal("0")
        cashflows: list[CashFlow] = []
        current_value = Decimal("0")

        for lot in lots:
            cost = lot.quantity * lot.price + lot.fees
            if lot.lot_type in (LotType.buy, LotType.contribution):
                total_invested += cost
                cashflows.append(CashFlow(date=lot.settled_at, amount=-float(cost)))
            elif lot.lot_type in (LotType.sell, LotType.withdrawal):
                proceeds = lot.quantity * lot.price - lot.fees
                cashflows.append(CashFlow(date=lot.settled_at, amount=float(proceeds)))
            elif lot.lot_type == LotType.dividend:
                cashflows.append(CashFlow(date=lot.settled_at, amount=float(lot.price)))

            # Current market value
            if lot.instrument_id and lot.lot_type == LotType.buy:
                price_result = await self.session.execute(
                    select(InstrumentPrice)
                    .where(
                        InstrumentPrice.instrument_id == lot.instrument_id,
                        InstrumentPrice.date <= today,
                    )
                    .order_by(InstrumentPrice.date.desc())
                    .limit(1)
                )
                latest_price = price_result.scalar_one_or_none()
                if latest_price:
                    current_value += lot.quantity * latest_price.close

        if current_value > Decimal("0"):
            cashflows.append(CashFlow(date=today, amount=float(current_value)))

        xirr_result = xirr(cashflows) if cashflows else None
        total_gain = current_value - total_invested
        gain_pct = float(total_gain / total_invested * 100) if total_invested else 0.0

        # TWR: simplified as total gain for now (proper TWR needs valuation at each CF date)
        twr_result = float(total_gain / total_invested) if total_invested else None

        return PerformanceOut(
            twr=twr_result,
            xirr=xirr_result,
            total_invested=total_invested,
            current_value=current_value,
            total_gain=total_gain,
            gain_pct=gain_pct,
            series=[],  # TODO: populate from snapshots for time series chart
        )

    # ── Allocation ────────────────────────────────────────────────────────

    async def get_allocation(self, scope: str = "household") -> AllocationOut:
        """Compute actual allocation by asset class, region, and wrapper."""
        lots_result = await self.session.execute(
            select(InvestmentLot).where(
                InvestmentLot.lot_type.in_([LotType.buy, LotType.contribution])
            )
        )
        lots = list(lots_result.scalars())
        today = datetime.date.today()

        holdings_by_class: dict[str, Decimal] = {}
        holdings_by_region: dict[str, Decimal] = {}
        holdings_by_wrapper: dict[str, Decimal] = {}

        total_value = Decimal("0")

        for lot in lots:
            if not lot.instrument_id:
                continue
            inst = await self.session.get(Instrument, lot.instrument_id)
            if not inst:
                continue

            price_result = await self.session.execute(
                select(InstrumentPrice)
                .where(
                    InstrumentPrice.instrument_id == lot.instrument_id,
                    InstrumentPrice.date <= today,
                )
                .order_by(InstrumentPrice.date.desc())
                .limit(1)
            )
            latest_price = price_result.scalar_one_or_none()
            if not latest_price:
                continue

            market_value = lot.quantity * latest_price.close
            total_value += market_value

            cls = inst.asset_class.value if inst.asset_class else "other"
            region = inst.region or "unknown"

            holdings_by_class[cls] = holdings_by_class.get(cls, Decimal("0")) + market_value
            holdings_by_region[region] = holdings_by_region.get(region, Decimal("0")) + market_value

            # Wrapper type from account
            from app.domains.accounts.models import Account
            account = await self.session.get(Account, lot.account_id)
            if account and account.wrapper_type:
                wt = account.wrapper_type.value
                holdings_by_wrapper[wt] = holdings_by_wrapper.get(wt, Decimal("0")) + market_value

        # Targets
        targets_result = await self.session.execute(select(TargetAllocation))
        targets = {t.asset_class: t.target_pct for t in targets_result.scalars()}

        def to_out(slices: list) -> list[AllocationSliceOut]:
            return [
                AllocationSliceOut(
                    asset_class=s.asset_class,
                    market_value=s.market_value,
                    actual_pct=s.actual_pct,
                    target_pct=s.target_pct,
                    drift_pct=s.drift_pct,
                )
                for s in slices
            ]

        return AllocationOut(
            total_value=total_value,
            by_class=to_out(compute_allocation(holdings_by_class, targets)),
            by_region=to_out(compute_allocation(holdings_by_region, {})),
            by_wrapper=to_out(compute_allocation(holdings_by_wrapper, {})),
        )

    async def set_target_allocation(self, body: TargetAllocationIn) -> None:
        for item in body.allocations:
            cls = str(item["asset_class"])
            pct = Decimal(str(item["target_pct"]))
            result = await self.session.execute(
                select(TargetAllocation).where(TargetAllocation.asset_class == cls)
            )
            existing = result.scalar_one_or_none()
            if existing:
                existing.target_pct = pct
            else:
                self.session.add(TargetAllocation(asset_class=cls, target_pct=pct))
        await self.session.flush()
