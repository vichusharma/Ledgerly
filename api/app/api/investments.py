"""Investments router — instruments, lots, prices, performance, allocation."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.domains.investments.schemas import (
    AllocationOut, HoldingCreateIn, HoldingOut, HoldingsOut,
    InstrumentCreateIn, InstrumentLookupOut, InstrumentOut,
    LotCreateIn, LotOut, PerformanceOut, PriceCreateIn, PriceOut,
    TargetAllocationIn,
)
from app.domains.investments.service import InvestmentService
from app.infra.price_provider import get_price_provider

router = APIRouter(tags=["investments"], dependencies=[Depends(get_current_user)])


# ── Instruments ───────────────────────────────────────────────────────────────

@router.get("/instruments", response_model=list[InstrumentOut])
async def list_instruments(db: AsyncSession = Depends(get_db)) -> list[InstrumentOut]:
    return await InvestmentService(db).list_instruments()


@router.post("/instruments", response_model=InstrumentOut, status_code=201)
async def create_instrument(body: InstrumentCreateIn, db: AsyncSession = Depends(get_db)) -> InstrumentOut:
    return await InvestmentService(db).create_instrument(body)


@router.get("/instruments/lookup", response_model=InstrumentLookupOut)
async def lookup_instrument(isin: str = Query(...), db: AsyncSession = Depends(get_db)) -> InstrumentLookupOut:
    """Read-only preview for the add-holding form — never writes to the DB.

    Registered before /instruments/{instrument_id} so "lookup" isn't swallowed
    as a path param.
    """
    provider = await get_price_provider(db)
    if provider is None:
        raise HTTPException(404, "Price lookup is disabled or not configured.")
    try:
        result = await provider.lookup(isin)
    except NotImplementedError:
        raise HTTPException(404, "Price lookup is disabled or not configured.")
    if result is None:
        raise HTTPException(404, "No match found for this ISIN.")
    return InstrumentLookupOut(
        isin=isin,
        symbol=result.symbol,
        name=result.name,
        ticker=result.ticker,
        currency=result.currency,
        price=result.price,
        price_date=result.price_date,
    )


@router.get("/instruments/{instrument_id}", response_model=InstrumentOut)
async def get_instrument(instrument_id: int, db: AsyncSession = Depends(get_db)) -> InstrumentOut:
    obj = await InvestmentService(db).get_instrument(instrument_id)
    if obj is None:
        raise HTTPException(404, "Instrument not found")
    return obj


# ── Investment lots ───────────────────────────────────────────────────────────

@router.get("/investment-lots", response_model=list[LotOut])
async def list_lots(
    account_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[LotOut]:
    return await InvestmentService(db).list_lots(account_id=account_id)


@router.post("/investment-lots", response_model=LotOut, status_code=201)
async def create_lot(body: LotCreateIn, db: AsyncSession = Depends(get_db)) -> LotOut:
    return await InvestmentService(db).create_lot(body)


@router.delete("/investment-lots/{lot_id}", status_code=204)
async def delete_lot(lot_id: int, db: AsyncSession = Depends(get_db)) -> None:
    await InvestmentService(db).delete_lot(lot_id)


# ── Prices ────────────────────────────────────────────────────────────────────

@router.post("/prices", response_model=PriceOut, status_code=201)
async def create_price(body: PriceCreateIn, db: AsyncSession = Depends(get_db)) -> PriceOut:
    return await InvestmentService(db).create_price(body)


@router.post("/prices/import")
async def import_prices(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    """Import EOD prices from CSV: columns isin,date,close."""
    content = await file.read()
    count = await InvestmentService(db).import_prices_csv(content)
    return {"imported": count}


# ── Performance ───────────────────────────────────────────────────────────────

@router.get("/portfolio/performance", response_model=PerformanceOut)
async def portfolio_performance(
    scope: str = "household",
    wrapper: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> PerformanceOut:
    return await InvestmentService(db).get_performance(scope=scope, wrapper=wrapper)


# ── Allocation ────────────────────────────────────────────────────────────────

@router.get("/portfolio/allocation", response_model=AllocationOut)
async def portfolio_allocation(
    scope: str = "household",
    db: AsyncSession = Depends(get_db),
) -> AllocationOut:
    return await InvestmentService(db).get_allocation(scope=scope)


@router.put("/portfolio/allocation/target", status_code=204)
async def set_target_allocation(
    body: TargetAllocationIn, db: AsyncSession = Depends(get_db)
) -> None:
    await InvestmentService(db).set_target_allocation(body)


# ── Holdings ──────────────────────────────────────────────────────────────────

@router.post("/portfolio/holdings", response_model=HoldingOut, status_code=201)
async def add_holding(body: HoldingCreateIn, db: AsyncSession = Depends(get_db)) -> HoldingOut:
    return await InvestmentService(db).add_holding(body)


@router.get("/portfolio/holdings", response_model=HoldingsOut)
async def portfolio_holdings(
    scope: str = "household",
    db: AsyncSession = Depends(get_db),
) -> HoldingsOut:
    return await InvestmentService(db).get_holdings(scope=scope)


# ── Tax hints (P3) ────────────────────────────────────────────────────────────

@router.get("/accounts/{account_id}/tax-hints")
async def account_tax_hints(
    account_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Return French tax-wrapper hints for an account (PEA clock, AV 8yr, etc.)."""
    import datetime
    from app.infra.tax_rules import get_wrapper_hints

    # Fetch the account to get wrapper_type + opened_at
    from app.domains.accounts.repository import AccountRepository
    account = await AccountRepository(db).get(account_id)
    if account is None:
        raise HTTPException(404, "Account not found")

    wrapper_type = account.wrapper_type.value if account.wrapper_type else None
    if wrapper_type is None:
        return []

    open_date = account.opened_at or account.created_at.date()
    hints = get_wrapper_hints(wrapper_type, open_date, datetime.date.today())
    return [
        {
            "key": h.key,
            "wrapper_type": h.wrapper_type,
            "message": h.message,
            "eligible": h.eligible,
            "eligible_date": h.eligible_date.isoformat() if h.eligible_date else None,
        }
        for h in hints
    ]
