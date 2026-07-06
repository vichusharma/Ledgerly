"""Unit tests for YahooFinancePriceProvider — mocked HTTP, no live network calls."""
from __future__ import annotations

import datetime
from decimal import Decimal
from unittest.mock import patch

from app.domains.investments.models import AssetClass
from app.infra.price_provider import YahooFinancePriceProvider

_SEARCH_URL = YahooFinancePriceProvider._SEARCH_URL
_CRUMB_URL = YahooFinancePriceProvider._CRUMB_URL
_COOKIE_URL = YahooFinancePriceProvider._COOKIE_URL
_CHART_PREFIX = "https://query1.finance.yahoo.com/v8/finance/chart/"


class _FakeResponse:
    def __init__(
        self, json_data: object = None, text_data: str = "", status_code: int = 200
    ) -> None:
        self._json = json_data
        self.text = text_data
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> object:
        return self._json


class _FakeAsyncClient:
    def __init__(self, *args: object, **kwargs: object) -> None:
        pass

    async def __aenter__(self) -> _FakeAsyncClient:
        return self

    async def __aexit__(self, *args: object) -> bool:
        return False

    async def get(self, url: str, params: dict | None = None, **kwargs: object) -> _FakeResponse:
        if url == _COOKIE_URL:
            return _FakeResponse(text_data="")
        if url == _CRUMB_URL:
            return _FakeResponse(text_data="fake-crumb")
        if url == _SEARCH_URL:
            q = (params or {}).get("q")
            if q == "IE00B4L5Y983":
                return _FakeResponse(json_data={
                    "quotes": [{
                        "symbol": "IWDA.AS", "quoteType": "ETF",
                        "shortname": "iShares Core MSCI World",
                    }]
                })
            if q == "LU0000000BND":
                return _FakeResponse(json_data={
                    "quotes": [{
                        "symbol": "GOVBND.PA", "quoteType": "MUTUALFUND",
                        "longname": "PIMCO Global Government Bond Fund",
                    }]
                })
            if q == "Acme Water":
                # Simulates the real-world case: the ISIN isn't indexed, but
                # a name search finds the fund (possibly under a different
                # currency share class than the one on the user's statement).
                return _FakeResponse(json_data={
                    "quotes": [
                        {"symbol": "0P00000001", "quoteType": "MUTUALFUND", "longname": "Acme Water P USD"},
                        {"symbol": "0P00000002", "quoteType": "MUTUALFUND", "longname": "Acme Water P EUR"},
                    ]
                })
            if q == "LU0000000JPY":
                # Real-world case reported by the user: this ISIN resolves to
                # a JPY share class, not the EUR one on the household's statement.
                return _FakeResponse(json_data={
                    "quotes": [{
                        "symbol": "0P0000JPYX", "quoteType": "MUTUALFUND",
                        "longname": "Some Japan Equity Fund P JPY",
                    }]
                })
            if q == "LU0NOFXRATE1":
                return _FakeResponse(json_data={
                    "quotes": [{
                        "symbol": "0P0000NOFX", "quoteType": "MUTUALFUND",
                        "longname": "No FX Rate Available Fund",
                    }]
                })
            return _FakeResponse(json_data={"quotes": []})
        if url.startswith(_CHART_PREFIX):
            symbol = url[len(_CHART_PREFIX):]
            if symbol == "NOFXEUR=X":
                # Simulates Yahoo having no FX-pair data for this currency.
                return _FakeResponse(json_data={"chart": {"result": []}})
            prices = {
                "0P00000001": (211.5, "USD"),
                "0P00000002": (194.3, "EUR"),
                "0P0000JPYX": (40451.6, "JPY"),
                "0P0000NOFX": (100.0, "NOFX"),
                "USDEUR=X": (0.92, "USD"),
                "JPYEUR=X": (0.0062, "JPY"),
            }
            price, currency = prices.get(symbol, (98.32, "EUR"))
            return _FakeResponse(json_data={
                "chart": {"result": [{"meta": {"regularMarketPrice": price, "currency": currency}}]}
            })
        raise AssertionError(f"unexpected URL requested in test: {url}")


@patch("httpx.AsyncClient", _FakeAsyncClient)
async def test_lookup_resolves_isin_to_price_and_metadata() -> None:
    provider = YahooFinancePriceProvider()
    result = await provider.lookup("IE00B4L5Y983")
    assert result is not None
    assert result.symbol == "IWDA.AS"
    assert result.name == "iShares Core MSCI World"
    assert result.price == Decimal("98.32")
    assert result.currency == "EUR"
    assert result.asset_class == AssetClass.equity


@patch("httpx.AsyncClient", _FakeAsyncClient)
async def test_lookup_guesses_bond_asset_class_from_fund_name() -> None:
    provider = YahooFinancePriceProvider()
    result = await provider.lookup("LU0000000BND")
    assert result is not None
    assert result.asset_class == AssetClass.bond


@patch("httpx.AsyncClient", _FakeAsyncClient)
async def test_lookup_returns_none_for_unresolvable_isin() -> None:
    provider = YahooFinancePriceProvider()
    result = await provider.lookup("NOTREALISIN01")
    assert result is None


@patch("httpx.AsyncClient", _FakeAsyncClient)
async def test_fetch_prices_omits_unresolvable_isin_without_raising() -> None:
    provider = YahooFinancePriceProvider()
    prices = await provider.fetch_prices(
        ["IE00B4L5Y983", "NOTREALISIN01"], datetime.date.today()
    )
    assert prices == {"IE00B4L5Y983": Decimal("98.32")}


@patch("httpx.AsyncClient", _FakeAsyncClient)
async def test_search_finds_multiple_candidates_by_name() -> None:
    provider = YahooFinancePriceProvider()
    results = await provider.search("Acme Water")
    assert {r.symbol for r in results} == {"0P00000001", "0P00000002"}
    usd = next(r for r in results if r.symbol == "0P00000001")
    eur = next(r for r in results if r.symbol == "0P00000002")
    # The USD share class gets converted to EUR at the source rather than
    # left in its native trading currency — every stored price/lot in this
    # app is assumed to be EUR.
    assert usd.name == "Acme Water P USD" and usd.currency == "EUR"
    assert usd.price == Decimal("211.5") * Decimal("0.92")
    assert eur.name == "Acme Water P EUR" and eur.currency == "EUR" and eur.price == Decimal("194.3")


@patch("httpx.AsyncClient", _FakeAsyncClient)
async def test_lookup_converts_non_eur_price_to_eur() -> None:
    """Real case reported by the user: LU0000000JPY resolves to a JPY share
    class on Yahoo, priced at 40451.6 — not EUR, despite the household's
    statement being EUR. lookup() must convert before returning."""
    provider = YahooFinancePriceProvider()
    result = await provider.lookup("LU0000000JPY")
    assert result is not None
    assert result.currency == "EUR"
    assert result.price == Decimal("40451.6") * Decimal("0.0062")


@patch("httpx.AsyncClient", _FakeAsyncClient)
async def test_fetch_price_by_symbol_converts_non_eur_currency() -> None:
    provider = YahooFinancePriceProvider()
    price = await provider.fetch_price_by_symbol("0P0000JPYX")
    assert price == Decimal("40451.6") * Decimal("0.0062")


@patch("httpx.AsyncClient", _FakeAsyncClient)
async def test_lookup_returns_none_when_fx_rate_unavailable() -> None:
    """If Yahoo has no FX-pair data for the fund's currency, we must not
    silently return a native-currency price mislabeled as EUR."""
    provider = YahooFinancePriceProvider()
    result = await provider.lookup("LU0NOFXRATE1")
    assert result is None


@patch("httpx.AsyncClient", _FakeAsyncClient)
async def test_search_returns_empty_list_for_no_matches() -> None:
    provider = YahooFinancePriceProvider()
    results = await provider.search("Nonexistent Fund Name XYZ")
    assert results == []


@patch("httpx.AsyncClient", _FakeAsyncClient)
async def test_fetch_price_by_symbol_skips_search_entirely() -> None:
    provider = YahooFinancePriceProvider()
    price = await provider.fetch_price_by_symbol("0P00000002")
    assert price == Decimal("194.3")
