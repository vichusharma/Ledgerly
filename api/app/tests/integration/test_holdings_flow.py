"""Integration tests — add-holding-by-ISIN and aggregated holdings view."""
from __future__ import annotations

import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.infra.price_provider import InstrumentLookupResult, InstrumentSearchResult
from app.domains.investments.models import AssetClass

pytestmark = pytest.mark.asyncio

PASSWORD = "S3cur3P@ss!"


def _fake_lookup_result(isin: str, price: float) -> InstrumentLookupResult:
    return InstrumentLookupResult(
        isin=isin, symbol="IWDA.AS", name="iShares Core MSCI World",
        ticker="IWDA", currency="EUR", price=Decimal(str(price)),
        price_date=datetime.date.today(), asset_class=AssetClass.equity,
    )


class _FakeProvider:
    def __init__(self, price: float) -> None:
        self._price = price

    async def lookup(self, isin: str) -> InstrumentLookupResult:
        return _fake_lookup_result(isin, self._price)


class _FakeUnresolvableIsinProvider:
    """Simulates a fund whose ISIN isn't indexed by the provider at all, but
    whose symbol (once resolved via search) can still be priced directly."""

    def __init__(self, symbol_prices: dict[str, float]) -> None:
        self._symbol_prices = symbol_prices

    async def lookup(self, isin: str) -> None:
        return None

    async def fetch_price_by_symbol(self, symbol: str) -> Decimal | None:
        price = self._symbol_prices.get(symbol)
        return Decimal(str(price)) if price is not None else None


class _FakeSearchProvider:
    async def search(self, query: str) -> list[InstrumentSearchResult]:
        if query != "Acme Water":
            return []
        return [
            InstrumentSearchResult(
                symbol="0P00000001", name="Acme Water P USD", currency="USD",
                price=Decimal("211.5"), price_date=datetime.date.today(),
                asset_class=AssetClass.equity,
            ),
            InstrumentSearchResult(
                symbol="0P00000002", name="Acme Water P EUR", currency="EUR",
                price=Decimal("194.3"), price_date=datetime.date.today(),
                asset_class=AssetClass.equity,
            ),
        ]


async def _setup(client: AsyncClient) -> dict:
    await client.post("/api/v1/auth/setup", json={"password": PASSWORD})
    await client.post("/api/v1/auth/login", json={"password": PASSWORD})
    person = (await client.post(
        "/api/v1/persons", json={"name": "Antoine", "is_primary": True}
    )).json()
    return (await client.post("/api/v1/accounts", json={
        "name": "CTO Boursorama", "type": "investment_wrapper",
        "wrapper_type": "CTO", "owner_id": person["id"],
    })).json()


async def test_add_holding_creates_instrument_lot_price_and_shows_in_holdings(
    client: AsyncClient,
) -> None:
    acct = await _setup(client)

    res = await client.post("/api/v1/portfolio/holdings", json={
        "isin": "IE00B4L5Y983",
        "quantity": 10,
        "account_id": acct["id"],
        "price": 98.32,
        "name": "iShares Core MSCI World",
        "ticker": "IWDA",
        "currency": "EUR",
    })
    assert res.status_code == 201
    body = res.json()
    assert body["instrument"]["isin"] == "IE00B4L5Y983"
    assert body["lot"]["lot_type"] == "buy"

    holdings = (await client.get("/api/v1/portfolio/holdings")).json()
    assert float(holdings["total_value"]) == pytest.approx(983.2)
    assert len(holdings["rows"]) == 1
    row = holdings["rows"][0]
    assert row["isin"] == "IE00B4L5Y983"
    assert float(row["quantity"]) == 10
    assert float(row["market_value"]) == pytest.approx(983.2)
    assert row["owner_name"] == "Antoine"
    assert row["account_name"] == "CTO Boursorama"


async def test_add_same_isin_twice_reuses_instrument_and_sums_quantity(
    client: AsyncClient,
) -> None:
    acct = await _setup(client)
    payload = {
        "isin": "IE00B4L5Y983", "quantity": 5, "account_id": acct["id"],
        "price": 100.0, "name": "iShares Core MSCI World",
    }
    r1 = await client.post("/api/v1/portfolio/holdings", json=payload)
    payload["quantity"] = 3
    payload["price"] = 102.0
    r2 = await client.post("/api/v1/portfolio/holdings", json=payload)

    assert r1.json()["instrument"]["id"] == r2.json()["instrument"]["id"]

    instruments = (await client.get("/api/v1/instruments")).json()
    assert len(instruments) == 1

    holdings = (await client.get("/api/v1/portfolio/holdings")).json()
    assert len(holdings["rows"]) == 1
    assert float(holdings["rows"][0]["quantity"]) == 8

    lots = (await client.get("/api/v1/investment-lots")).json()
    assert len(lots) == 2


async def test_instrument_lookup_is_disabled_by_default(client: AsyncClient) -> None:
    await _setup(client)
    res = await client.get("/api/v1/instruments/lookup", params={"isin": "IE00B4L5Y983"})
    assert res.status_code == 404


async def test_sell_lot_reduces_quantity_and_cost_basis_at_average_cost(
    client: AsyncClient,
) -> None:
    acct = await _setup(client)
    add = await client.post("/api/v1/portfolio/holdings", json={
        "isin": "IE00B4L5Y983", "quantity": 10, "account_id": acct["id"],
        "price": 100.0, "name": "iShares Core MSCI World",
    })
    instrument_id = add.json()["instrument"]["id"]

    sell = await client.post("/api/v1/investment-lots", json={
        "account_id": acct["id"], "instrument_id": instrument_id,
        "lot_type": "sell", "quantity": 4, "price": 110.0,
        "settled_at": "2026-07-01",
    })
    assert sell.status_code == 201

    holdings = (await client.get("/api/v1/portfolio/holdings")).json()
    assert len(holdings["rows"]) == 1
    row = holdings["rows"][0]
    assert float(row["quantity"]) == 6
    # Average cost was 100/unit; selling 4 of 10 removes 4*100 = 400 of cost basis.
    assert float(row["cost_basis"]) == pytest.approx(600.0)
    assert float(row["market_value"]) == pytest.approx(600.0)  # priced at 100/unit still

    alloc = (await client.get("/api/v1/portfolio/allocation")).json()
    assert float(alloc["total_value"]) == pytest.approx(600.0)


async def test_fully_sold_position_disappears_from_holdings(client: AsyncClient) -> None:
    acct = await _setup(client)
    add = await client.post("/api/v1/portfolio/holdings", json={
        "isin": "IE00B4L5Y983", "quantity": 5, "account_id": acct["id"],
        "price": 100.0, "name": "iShares Core MSCI World",
    })
    instrument_id = add.json()["instrument"]["id"]

    await client.post("/api/v1/investment-lots", json={
        "account_id": acct["id"], "instrument_id": instrument_id,
        "lot_type": "sell", "quantity": 5, "price": 110.0,
        "settled_at": "2026-07-01",
    })

    holdings = (await client.get("/api/v1/portfolio/holdings")).json()
    assert holdings["rows"] == []
    assert float(holdings["total_value"]) == 0.0


async def test_performance_and_allocation_unaffected_by_positions_refactor(
    client: AsyncClient,
) -> None:
    acct = await _setup(client)
    await client.post("/api/v1/portfolio/holdings", json={
        "isin": "IE00B4L5Y983", "quantity": 10, "account_id": acct["id"],
        "price": 100.0, "name": "iShares Core MSCI World", "asset_class": "equity",
    })

    perf = (await client.get("/api/v1/portfolio/performance")).json()
    assert float(perf["current_value"]) == pytest.approx(1000.0)
    assert float(perf["total_invested"]) == pytest.approx(1000.0)

    alloc = (await client.get("/api/v1/portfolio/allocation")).json()
    assert float(alloc["total_value"]) == pytest.approx(1000.0)
    equity_slice = next(s for s in alloc["by_class"] if s["asset_class"] == "equity")
    assert float(equity_slice["market_value"]) == pytest.approx(1000.0)


async def test_update_quantity_requires_lookup_enabled(client: AsyncClient) -> None:
    acct = await _setup(client)
    add = await client.post("/api/v1/portfolio/holdings", json={
        "isin": "IE00B4L5Y983", "quantity": 10, "account_id": acct["id"],
        "price": 100.0, "name": "iShares Core MSCI World",
    })
    instrument_id = add.json()["instrument"]["id"]

    res = await client.put("/api/v1/portfolio/holdings/quantity", json={
        "account_id": acct["id"], "instrument_id": instrument_id, "quantity": 12,
    })
    assert res.status_code == 422


@patch(
    "app.infra.price_provider.get_price_provider",
    new=AsyncMock(return_value=_FakeProvider(price=105.0)),
)
async def test_increasing_quantity_adds_buy_lot_and_grows_cost_basis(
    client: AsyncClient,
) -> None:
    acct = await _setup(client)
    await client.put("/api/v1/settings/price-lookup", json={"price_lookup_enabled": True})
    add = await client.post("/api/v1/portfolio/holdings", json={
        "isin": "IE00B4L5Y983", "quantity": 10, "account_id": acct["id"],
        "price": 100.0, "name": "iShares Core MSCI World",
    })
    instrument_id = add.json()["instrument"]["id"]

    res = await client.put("/api/v1/portfolio/holdings/quantity", json={
        "account_id": acct["id"], "instrument_id": instrument_id, "quantity": 15,
    })
    assert res.status_code == 200
    row = res.json()
    assert float(row["quantity"]) == 15
    # 10 @ 100 + 5 @ 105 = 1525 cost basis; priced at latest lookup (105) = 1575 market value.
    assert float(row["cost_basis"]) == pytest.approx(1525.0)
    assert float(row["market_value"]) == pytest.approx(1575.0)

    lots = (await client.get("/api/v1/investment-lots")).json()
    buy_lots = [l for l in lots if l["lot_type"] == "buy"]
    assert len(buy_lots) == 2  # original add-holding lot + the delta lot


@patch(
    "app.infra.price_provider.get_price_provider",
    new=AsyncMock(return_value=_FakeProvider(price=105.0)),
)
async def test_decreasing_quantity_adds_sell_lot_and_shrinks_cost_basis(
    client: AsyncClient,
) -> None:
    acct = await _setup(client)
    await client.put("/api/v1/settings/price-lookup", json={"price_lookup_enabled": True})
    add = await client.post("/api/v1/portfolio/holdings", json={
        "isin": "IE00B4L5Y983", "quantity": 10, "account_id": acct["id"],
        "price": 100.0, "name": "iShares Core MSCI World",
    })
    instrument_id = add.json()["instrument"]["id"]

    res = await client.put("/api/v1/portfolio/holdings/quantity", json={
        "account_id": acct["id"], "instrument_id": instrument_id, "quantity": 4,
    })
    assert res.status_code == 200
    row = res.json()
    assert float(row["quantity"]) == 4
    assert float(row["cost_basis"]) == pytest.approx(400.0)
    assert float(row["market_value"]) == pytest.approx(420.0)  # 4 @ 105

    lots = (await client.get("/api/v1/investment-lots")).json()
    sell_lots = [l for l in lots if l["lot_type"] == "sell"]
    assert len(sell_lots) == 1
    assert float(sell_lots[0]["quantity"]) == 6


@patch(
    "app.infra.price_provider.get_price_provider",
    new=AsyncMock(return_value=_FakeProvider(price=99.0)),
)
async def test_no_op_quantity_still_refreshes_price(client: AsyncClient) -> None:
    acct = await _setup(client)
    await client.put("/api/v1/settings/price-lookup", json={"price_lookup_enabled": True})
    add = await client.post("/api/v1/portfolio/holdings", json={
        "isin": "IE00B4L5Y983", "quantity": 10, "account_id": acct["id"],
        "price": 100.0, "name": "iShares Core MSCI World",
    })
    instrument_id = add.json()["instrument"]["id"]

    res = await client.put("/api/v1/portfolio/holdings/quantity", json={
        "account_id": acct["id"], "instrument_id": instrument_id, "quantity": 10,
    })
    assert res.status_code == 200
    row = res.json()
    assert float(row["quantity"]) == 10
    assert float(row["market_value"]) == pytest.approx(990.0)  # repriced at 99, not 100

    lots = (await client.get("/api/v1/investment-lots")).json()
    assert len(lots) == 1  # no new lot created for a zero-delta edit


@patch(
    "app.infra.price_provider.get_price_provider",
    new=AsyncMock(return_value=_FakeProvider(price=105.0)),
)
async def test_selling_down_to_zero_returns_204_and_removes_from_holdings(
    client: AsyncClient,
) -> None:
    acct = await _setup(client)
    await client.put("/api/v1/settings/price-lookup", json={"price_lookup_enabled": True})
    add = await client.post("/api/v1/portfolio/holdings", json={
        "isin": "IE00B4L5Y983", "quantity": 10, "account_id": acct["id"],
        "price": 100.0, "name": "iShares Core MSCI World",
    })
    instrument_id = add.json()["instrument"]["id"]

    res = await client.put("/api/v1/portfolio/holdings/quantity", json={
        "account_id": acct["id"], "instrument_id": instrument_id, "quantity": 0,
    })
    assert res.status_code == 204

    holdings = (await client.get("/api/v1/portfolio/holdings")).json()
    assert holdings["rows"] == []


@patch(
    "app.api.investments.get_price_provider",
    new=AsyncMock(return_value=_FakeSearchProvider()),
)
async def test_instrument_search_finds_candidates_by_name(client: AsyncClient) -> None:
    await _setup(client)
    res = await client.get("/api/v1/instruments/search", params={"q": "Acme Water"})
    assert res.status_code == 200
    results = res.json()
    assert {r["symbol"] for r in results} == {"0P00000001", "0P00000002"}
    eur = next(r for r in results if r["symbol"] == "0P00000002")
    assert eur["name"] == "Acme Water P EUR"
    assert float(eur["price"]) == pytest.approx(194.3)


@patch(
    "app.api.investments.get_price_provider",
    new=AsyncMock(return_value=_FakeSearchProvider()),
)
async def test_instrument_search_empty_for_no_matches(client: AsyncClient) -> None:
    await _setup(client)
    res = await client.get("/api/v1/instruments/search", params={"q": "Nothing Matches This"})
    assert res.status_code == 200
    assert res.json() == []


async def test_update_quantity_prefers_stored_ticker_when_isin_unresolvable(
    client: AsyncClient,
) -> None:
    """Reproduces a real case: a fund's ISIN (e.g. a French AV share class)
    isn't indexed by the price provider's ISIN search at all, but its symbol
    — found once via the name-search fallback and stored as Instrument.ticker
    — can still be priced directly, skipping ISIN search entirely."""
    acct = await _setup(client)
    with patch(
        "app.infra.price_provider.get_price_provider",
        new=AsyncMock(return_value=_FakeProvider(price=100.0)),
    ):
        await client.put("/api/v1/settings/price-lookup", json={"price_lookup_enabled": True})
        add = await client.post("/api/v1/portfolio/holdings", json={
            "isin": "LU0000000WTR", "quantity": 10, "account_id": acct["id"],
            "price": 194.3, "name": "Acme Water P EUR", "ticker": "0P00000002",
        })
    instrument_id = add.json()["instrument"]["id"]

    with patch(
        "app.infra.price_provider.get_price_provider",
        new=AsyncMock(return_value=_FakeUnresolvableIsinProvider({"0P00000002": 205.0})),
    ):
        res = await client.put("/api/v1/portfolio/holdings/quantity", json={
            "account_id": acct["id"], "instrument_id": instrument_id, "quantity": 15,
        })
    assert res.status_code == 200
    row = res.json()
    assert float(row["quantity"]) == 15
    assert float(row["market_value"]) == pytest.approx(15 * 205.0)


async def test_update_quantity_fails_clearly_when_ticker_and_isin_both_unresolvable(
    client: AsyncClient,
) -> None:
    acct = await _setup(client)
    with patch(
        "app.infra.price_provider.get_price_provider",
        new=AsyncMock(return_value=_FakeProvider(price=100.0)),
    ):
        await client.put("/api/v1/settings/price-lookup", json={"price_lookup_enabled": True})
        add = await client.post("/api/v1/portfolio/holdings", json={
            "isin": "LU0000000WTR", "quantity": 10, "account_id": acct["id"],
            "price": 194.3, "name": "Acme Water P EUR", "ticker": "0P00000002",
        })
    instrument_id = add.json()["instrument"]["id"]

    with patch(
        "app.infra.price_provider.get_price_provider",
        new=AsyncMock(return_value=_FakeUnresolvableIsinProvider({})),  # no symbol resolves either
    ):
        res = await client.put("/api/v1/portfolio/holdings/quantity", json={
            "account_id": acct["id"], "instrument_id": instrument_id, "quantity": 15,
        })
    assert res.status_code == 422
