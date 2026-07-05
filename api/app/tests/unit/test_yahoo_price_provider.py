"""Unit tests for YahooFinancePriceProvider — mocked HTTP, no live network calls."""
from __future__ import annotations

import datetime
from decimal import Decimal
from unittest.mock import patch

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
            isin = (params or {}).get("q")
            if isin == "IE00B4L5Y983":
                return _FakeResponse(json_data={
                    "quotes": [{
                        "symbol": "IWDA.AS", "quoteType": "ETF",
                        "shortname": "iShares Core MSCI World",
                    }]
                })
            return _FakeResponse(json_data={"quotes": []})
        if url.startswith(_CHART_PREFIX):
            return _FakeResponse(json_data={
                "chart": {"result": [{"meta": {"regularMarketPrice": 98.32, "currency": "EUR"}}]}
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
