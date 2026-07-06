"""Investments service — instruments, lots, prices, TWR/XIRR, allocation."""
from __future__ import annotations

import csv
import datetime
import io
from dataclasses import dataclass
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
    AllocationOut, AllocationSliceOut, HoldingCreateIn, HoldingOut,
    HoldingQuantityUpdateIn, HoldingRowOut, HoldingsOut, InstrumentCreateIn,
    InstrumentOut, LotCreateIn, LotOut, PerformanceOut, PerformanceSeriesPoint,
    PriceCreateIn, PriceOut, TargetAllocationIn,
)


@dataclass(frozen=True)
class PositionSnapshot:
    """A current position derived from the lot ledger — one per (account, instrument),
    or one per instrument for statement valuations (which supersede globally, not
    per-account — see `_latest_valuations`), or one per account for cash-only buy
    lots (`instrument_id is None`)."""

    account_id: int
    instrument_id: int | None
    quantity: Decimal
    cost_basis: Decimal | None  # None for valuation-sourced rows (not a purchase)
    price: Decimal | None
    price_date: datetime.date | None
    market_value: Decimal | None  # None when no price is available yet
    source: str  # "valuation" | "buy" | "cash"


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
        if body.isin:
            existing = await self.session.execute(
                select(Instrument).where(Instrument.isin == body.isin)
            )
            found = existing.scalar_one_or_none()
            if found:
                return InstrumentOut.model_validate(found)

        inst = Instrument(**body.model_dump())
        try:
            # Savepoint so a lost create-race doesn't roll back other writes
            # already made earlier in this session/request.
            async with self.session.begin_nested():
                self.session.add(inst)
                await self.session.flush()
        except IntegrityError:
            # Lost a create-race on the unique ISIN — the other insert won, reuse it.
            existing = await self.session.execute(
                select(Instrument).where(Instrument.isin == body.isin)
            )
            return InstrumentOut.model_validate(existing.scalar_one())
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
        try:
            # Savepoint so a duplicate (instrument, date) doesn't roll back
            # other writes already made earlier in this session/request (e.g.
            # add_holding's lot insert that precedes this price upsert).
            async with self.session.begin_nested():
                self.session.add(price)
                await self.session.flush()
        except IntegrityError:
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

    # ── Valuation lots ────────────────────────────────────────────────────

    @staticmethod
    def _latest_valuations(lots: list[InvestmentLot]) -> dict[int, InvestmentLot]:
        """instrument_id → most recent valuation lot (each supersedes earlier ones)."""
        best: dict[int, InvestmentLot] = {}
        for lot in lots:
            if lot.lot_type != LotType.valuation or not lot.instrument_id:
                continue
            cur = best.get(lot.instrument_id)
            if cur is None or (lot.settled_at, lot.id) > (cur.settled_at, cur.id):
                best[lot.instrument_id] = lot
        return best

    async def _compute_positions(
        self, lots: list[InvestmentLot], as_of: datetime.date
    ) -> list[PositionSnapshot]:
        """Derive current positions from a lot ledger.

        Shared by get_performance, get_allocation, and
        networth/service.py::_compute_account_balance so the "latest valuation
        wins, else sum buy-lot quantity x latest price" algorithm exists in one
        place. Statement valuations supersede globally per instrument (not per
        account) — see `_latest_valuations` — exactly as before this helper
        existed; callers that want only priced instrument positions should
        filter out `source == "cash"` rows (instrument_id is None) themselves.
        """
        relevant = [
            lot for lot in lots
            if lot.lot_type in (LotType.buy, LotType.sell, LotType.valuation)
            and lot.settled_at <= as_of
        ]
        valuations = self._latest_valuations(relevant)

        positions: list[PositionSnapshot] = [
            PositionSnapshot(
                account_id=lot.account_id,
                instrument_id=lot.instrument_id,
                quantity=lot.quantity,
                cost_basis=None,
                price=lot.price,
                price_date=lot.settled_at,
                market_value=lot.quantity * lot.price,
                source="valuation",
            )
            for lot in valuations.values()
        ]

        # Average-cost accounting (not FIFO/LIFO tax-lot matching): buys and
        # sells for the same (account, instrument) are netted into a single
        # quantity/cost-basis pair, with sells reducing cost basis at the
        # average cost per unit of everything bought so far. Sufficient for a
        # personal net-worth tool; not a substitute for real capital-gains
        # tax-lot tracking.
        grouped: dict[tuple[int, int], dict[str, Decimal]] = {}
        cash_grouped: dict[int, dict[str, Decimal]] = {}
        for lot in relevant:
            if lot.lot_type == LotType.buy and lot.instrument_id is None:
                g = cash_grouped.setdefault(
                    lot.account_id, {"quantity": Decimal("0"), "cost_basis": Decimal("0")}
                )
                g["quantity"] += lot.quantity
                g["cost_basis"] += lot.quantity * lot.price
                continue
            if lot.lot_type not in (LotType.buy, LotType.sell) or not lot.instrument_id:
                continue
            if lot.instrument_id in valuations:
                continue  # statement value supersedes computed value
            key = (lot.account_id, lot.instrument_id)
            g = grouped.setdefault(
                key,
                {
                    "buy_quantity": Decimal("0"), "buy_cost_basis": Decimal("0"),
                    "sell_quantity": Decimal("0"),
                },
            )
            if lot.lot_type == LotType.buy:
                g["buy_quantity"] += lot.quantity
                g["buy_cost_basis"] += lot.quantity * lot.price + lot.fees
            else:
                g["sell_quantity"] += lot.quantity

        price_cache: dict[int, InstrumentPrice | None] = {}
        for (account_id, instrument_id), g in grouped.items():
            net_quantity = g["buy_quantity"] - g["sell_quantity"]
            if net_quantity <= 0:
                continue  # fully (or over-)sold — no current position
            avg_cost_per_unit = (
                g["buy_cost_basis"] / g["buy_quantity"] if g["buy_quantity"] else Decimal("0")
            )
            cost_basis = avg_cost_per_unit * net_quantity

            if instrument_id not in price_cache:
                price_result = await self.session.execute(
                    select(InstrumentPrice)
                    .where(
                        InstrumentPrice.instrument_id == instrument_id,
                        InstrumentPrice.date <= as_of,
                    )
                    .order_by(InstrumentPrice.date.desc())
                    .limit(1)
                )
                price_cache[instrument_id] = price_result.scalar_one_or_none()
            price_row = price_cache[instrument_id]
            positions.append(PositionSnapshot(
                account_id=account_id,
                instrument_id=instrument_id,
                quantity=net_quantity,
                cost_basis=cost_basis,
                price=price_row.close if price_row else None,
                price_date=price_row.date if price_row else None,
                market_value=net_quantity * price_row.close if price_row else None,
                source="buy",
            ))

        for account_id, g in cash_grouped.items():
            positions.append(PositionSnapshot(
                account_id=account_id,
                instrument_id=None,
                quantity=g["quantity"],
                cost_basis=g["cost_basis"],
                price=None,
                price_date=None,
                market_value=g["cost_basis"],
                source="cash",
            ))

        return positions

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

        # Current value comes from the shared positions helper — only instrument
        # positions count (cash-only buy lots are a networth-only concept).
        positions = await self._compute_positions(lots, today)
        priced = (
            p.market_value for p in positions
            if p.instrument_id is not None and p.market_value is not None
        )
        current_value = sum(priced, Decimal("0"))

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
                InvestmentLot.lot_type.in_(
                    [LotType.buy, LotType.sell, LotType.contribution, LotType.valuation]
                )
            )
        )
        lots = list(lots_result.scalars())
        today = datetime.date.today()

        holdings_by_class: dict[str, Decimal] = {}
        holdings_by_region: dict[str, Decimal] = {}
        holdings_by_wrapper: dict[str, Decimal] = {}

        total_value = Decimal("0")

        from app.domains.accounts.models import Account, WrapperType

        positions = await self._compute_positions(lots, today)
        instrument_cache: dict[int, Instrument] = {}
        account_cache: dict[int, Account] = {}

        for p in positions:
            if p.instrument_id is None or p.market_value is None:
                continue

            inst = instrument_cache.get(p.instrument_id)
            if inst is None:
                inst = await self.session.get(Instrument, p.instrument_id)
                if inst is None:
                    continue
                instrument_cache[p.instrument_id] = inst

            market_value = p.market_value
            total_value += market_value

            # asset_class/wrapper_type columns are plain String (not SQLAlchemy
            # Enum), so a DB round-trip yields a raw str, not the enum member —
            # normalize via the enum's value-lookup constructor before .value.
            cls = AssetClass(inst.asset_class).value if inst.asset_class else "other"
            region = inst.region or "unknown"

            holdings_by_class[cls] = holdings_by_class.get(cls, Decimal("0")) + market_value
            holdings_by_region[region] = holdings_by_region.get(region, Decimal("0")) + market_value

            account = account_cache.get(p.account_id)
            if account is None:
                account = await self.session.get(Account, p.account_id)
                if account is not None:
                    account_cache[p.account_id] = account
            if account and account.wrapper_type:
                wt = WrapperType(account.wrapper_type).value
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

    # ── Holdings (composite add-by-ISIN + aggregated positions) ─────────────

    async def add_holding(self, body: HoldingCreateIn) -> HoldingOut:
        """Resolve/create the instrument by ISIN, record a buy lot, and stamp
        today's (or the given) price so the position shows correctly without
        waiting for the daily price-fetch job."""
        settled_at = body.settled_at or datetime.date.today()
        instrument = await self.create_instrument(InstrumentCreateIn(
            isin=body.isin,
            ticker=body.ticker,
            name=body.name or body.ticker or body.isin,
            asset_class=body.asset_class,
            currency=body.currency or "EUR",
        ))
        lot = await self.create_lot(LotCreateIn(
            account_id=body.account_id,
            instrument_id=instrument.id,
            lot_type=LotType.buy,
            quantity=body.quantity,
            price=body.price,
            fees=body.fees,
            currency=instrument.currency,
            settled_at=settled_at,
            notes=body.notes,
        ))
        await self.create_price(PriceCreateIn(
            instrument_id=instrument.id,
            date=settled_at,
            close=body.price,
            currency=instrument.currency,
        ))
        return HoldingOut(lot=lot, instrument=instrument)

    async def update_holding_quantity(
        self, body: HoldingQuantityUpdateIn
    ) -> HoldingRowOut | None:
        """Edit a holding's quantity in place: records a `buy` (increase) or
        `sell` (decrease) lot for the delta at a freshly looked-up market
        price, so full buy/sell history and cost basis are preserved — this
        is not a snapshot overwrite. Always refreshes the stamped price, even
        when quantity is unchanged, so market value stays current.

        Returns None only when the edit fully liquidates the position (new
        quantity 0 — router → 204 No Content). All other failures (unknown
        instrument, no ISIN, lookup unavailable) raise ValueError (router →
        422) — this is the only method's sole "success but nothing to show"
        outcome, so a None return is unambiguous.
        """
        from app.infra.price_provider import get_price_provider

        instrument = await self.session.get(Instrument, body.instrument_id)
        if instrument is None:
            raise ValueError("Instrument not found.")
        if not instrument.isin:
            raise ValueError("Only ISIN-backed holdings can have their quantity edited.")

        settled_at = body.settled_at or datetime.date.today()
        today = datetime.date.today()

        lots_result = await self.session.execute(
            select(InvestmentLot).where(
                InvestmentLot.account_id == body.account_id,
                InvestmentLot.instrument_id == body.instrument_id,
                InvestmentLot.lot_type.in_([LotType.buy, LotType.sell]),
            )
        )
        lots = list(lots_result.scalars())
        positions = await self._compute_positions(lots, today)
        current_quantity = positions[0].quantity if positions else Decimal("0")

        provider = await get_price_provider(self.session)
        if provider is None:
            raise ValueError(
                "Enable automatic price lookup in Settings to update this holding."
            )
        price: Decimal | None = None
        if instrument.ticker:
            # Prefer the already-resolved symbol — some funds' ISINs aren't
            # indexed by the provider's search at all (common for European
            # insurance-wrapped share classes), even though the fund itself
            # is reachable once a symbol has been found once via search().
            try:
                price = await provider.fetch_price_by_symbol(instrument.ticker)
            except NotImplementedError:
                price = None
        if price is None:
            result = await provider.lookup(instrument.isin)
            price = result.price if result else None
        if price is None:
            raise ValueError(
                "Couldn't fetch a current price for this holding. "
                "Enable automatic price lookup in Settings, or re-add it via search if its ISIN isn't found."
            )

        delta = body.quantity - current_quantity
        if delta > 0:
            await self.create_lot(LotCreateIn(
                account_id=body.account_id,
                instrument_id=body.instrument_id,
                lot_type=LotType.buy,
                quantity=delta,
                price=price,
                currency=instrument.currency,
                settled_at=settled_at,
            ))
        elif delta < 0:
            await self.create_lot(LotCreateIn(
                account_id=body.account_id,
                instrument_id=body.instrument_id,
                lot_type=LotType.sell,
                quantity=-delta,
                price=price,
                currency=instrument.currency,
                settled_at=settled_at,
            ))

        await self.create_price(PriceCreateIn(
            instrument_id=instrument.id,
            date=settled_at,
            close=price,
            currency=instrument.currency,
        ))

        from app.domains.networth.service import NetWorthService
        await NetWorthService(self.session).take_snapshot()

        holdings = await self.get_holdings("household")
        for row in holdings.rows:
            if row.account_id == body.account_id and row.instrument_id == body.instrument_id:
                return row
        return None  # fully sold via this edit — no position left to show

    async def get_holdings(self, scope: str = "household") -> HoldingsOut:
        """Aggregate current positions (per account+instrument) for display."""
        from app.domains.accounts.models import WrapperType
        from app.domains.accounts.repository import AccountRepository, PersonRepository

        person_repo = PersonRepository(self.session)
        account_repo = AccountRepository(self.session)
        persons = await person_repo.list_persons()
        if scope == "household":
            person_ids = [p.id for p in persons]
        else:
            try:
                person_ids = [int(scope)]
            except ValueError:
                person_ids = [p.id for p in persons]

        accounts = await account_repo.list_accounts(person_ids=person_ids, include_archived=False)
        allowed_account_ids = {a.id for a in accounts}
        if not allowed_account_ids:
            return HoldingsOut(total_value=Decimal("0"), rows=[])

        lots_result = await self.session.execute(
            select(InvestmentLot).where(
                InvestmentLot.lot_type.in_([LotType.buy, LotType.sell, LotType.valuation]),
                InvestmentLot.account_id.in_(allowed_account_ids),
            )
        )
        lots = list(lots_result.scalars())
        today = datetime.date.today()
        positions = [
            p for p in await self._compute_positions(lots, today) if p.instrument_id is not None
        ]

        total_value = sum(
            (p.market_value for p in positions if p.market_value is not None), Decimal("0")
        )

        account_map = {a.id: a for a in accounts}
        person_map = {p.id: p for p in persons}
        instrument_cache: dict[int, Instrument] = {}

        rows: list[HoldingRowOut] = []
        for p in positions:
            account = account_map.get(p.account_id)
            if account is None:
                continue
            inst = instrument_cache.get(p.instrument_id)
            if inst is None:
                inst = await self.session.get(Instrument, p.instrument_id)
                if inst is None:
                    continue
                instrument_cache[p.instrument_id] = inst

            owner = person_map.get(account.owner_id)
            joint_owner = person_map.get(account.joint_owner_id) if account.joint_owner_id else None

            gain_loss: Decimal | None = None
            gain_loss_pct: float | None = None
            if p.cost_basis is not None and p.market_value is not None:
                gain_loss = p.market_value - p.cost_basis
                if p.cost_basis:
                    gain_loss_pct = float(gain_loss / p.cost_basis * 100)

            weight_pct = (
                (p.market_value / total_value * 100)
                if p.market_value is not None and total_value
                else Decimal("0")
            )

            rows.append(HoldingRowOut(
                account_id=account.id,
                account_name=account.name,
                wrapper_type=(
                    WrapperType(account.wrapper_type).value if account.wrapper_type else None
                ),
                owner_name=owner.name if owner else "",
                joint_owner_name=joint_owner.name if joint_owner else None,
                ownership_pct=account.ownership_pct,
                instrument_id=inst.id,
                isin=inst.isin,
                ticker=inst.ticker,
                name=inst.name,
                asset_class=inst.asset_class,
                quantity=p.quantity,
                price=p.price,
                price_date=p.price_date,
                market_value=p.market_value,
                cost_basis=p.cost_basis,
                gain_loss=gain_loss,
                gain_loss_pct=gain_loss_pct,
                weight_pct=weight_pct,
                source=p.source,
            ))

        rows.sort(key=lambda r: (r.market_value is None, -(r.market_value or Decimal("0"))))

        return HoldingsOut(total_value=total_value, rows=rows)
