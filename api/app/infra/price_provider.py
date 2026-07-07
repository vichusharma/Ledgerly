"""
Pluggable price provider interface.

Disabled by default (the "100% local" promise). When enabled:
- Only fetches PRICES — never sends holdings, quantities, or account
  identifiers, only ISIN codes (and, for lookup, a single ISIN at a time)
- Two opt-in paths, checked in this order:
  1. `settings.price_provider_url` — an explicit self-hosted/advanced
     override (`HttpPriceProvider`), unconditionally enabled if set.
  2. The household's `price_lookup_enabled` flag (set via the Settings UI
     toggle) — uses the built-in `YahooFinancePriceProvider`, which needs no
     signup/API key.
- Otherwise, disabled: `get_price_provider()` returns None.

Usage:
    provider = await get_price_provider(session)
    if provider:
        prices = await provider.fetch_prices(["IE00B4L5Y983"], date.today())
"""
from __future__ import annotations

import asyncio
import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.investments.models import AssetClass
from app.infra.settings import get_settings

# Best-effort keyword buckets for guessing asset class from a fund's name —
# Yahoo's quoteType (EQUITY/ETF/MUTUALFUND/INDEX) alone can't distinguish a
# bond fund from an equity fund. Not authoritative; always user-overridable.
_ASSET_CLASS_KEYWORDS: dict[AssetClass, tuple[str, ...]] = {
    AssetClass.bond: ("bond", "obligation", "oblig", "gov", "treasury", "gilt"),
    AssetClass.cash: ("money market", "cash", "liquidit"),
    AssetClass.commodity: ("gold", "commodity", "metal", "silver", "oil"),
}


def _guess_asset_class(quote: dict) -> AssetClass:
    name = f"{quote.get('longname', '')} {quote.get('shortname', '')}".lower()
    for asset_class, keywords in _ASSET_CLASS_KEYWORDS.items():
        if any(kw in name for kw in keywords):
            return asset_class
    return AssetClass.equity


@dataclass(frozen=True)
class InstrumentLookupResult:
    isin: str
    symbol: str
    name: str
    ticker: str | None
    currency: str
    price: Decimal
    price_date: datetime.date
    asset_class: AssetClass


@dataclass(frozen=True)
class InstrumentSearchResult:
    """A name-search candidate — used when a fund's ISIN isn't indexed by the
    provider's ISIN search (common for European insurance-wrapped fund share
    classes) but the fund is still findable by name under a plain symbol."""
    symbol: str
    name: str
    currency: str
    price: Decimal
    price_date: datetime.date
    asset_class: AssetClass


class BasePriceProvider(ABC):
    """Abstract price provider — implementations must not send user holdings."""

    @abstractmethod
    async def fetch_prices(
        self,
        isins: list[str],
        date: datetime.date,
    ) -> dict[str, Decimal]:
        """
        Fetch closing prices for the given ISINs on the given date.

        Args:
            isins: List of ISIN codes to fetch prices for.
            date: The date for which to fetch prices.

        Returns:
            Dict mapping ISIN → closing price in the instrument's native currency.
            ISINs that can't be resolved/priced are simply omitted — one bad
            ISIN must never abort the whole batch.

        IMPORTANT: This method MUST NOT include any user data (portfolio holdings,
        quantities, account identifiers) in the outbound request.
        """
        ...

    async def lookup(self, isin: str) -> InstrumentLookupResult | None:
        """Resolve metadata + current price for a single ISIN (add-holding preview).

        Optional — providers that only support the batch price fetch (e.g. a
        self-hosted `HttpPriceProvider`) don't need to implement this; callers
        should treat `NotImplementedError` as "lookup not supported."
        """
        raise NotImplementedError

    async def search(self, query: str) -> list[InstrumentSearchResult]:
        """Find candidate instruments by free-text name — fallback for when
        `lookup(isin)` finds nothing (the ISIN isn't indexed by the provider,
        even though the fund exists there under a plain symbol).

        Optional — same NotImplementedError contract as `lookup`.
        """
        raise NotImplementedError

    async def fetch_price_by_symbol(self, symbol: str) -> Decimal | None:
        """Fetch the current price for an already-resolved provider symbol,
        skipping name/ISIN search entirely. Used to refresh a holding whose
        ISIN was never resolvable, once its symbol was found once via
        `search()` and stored on the Instrument.

        Optional — same NotImplementedError contract as `lookup`.
        """
        raise NotImplementedError


class HttpPriceProvider(BasePriceProvider):
    """
    Generic HTTP price provider stub — for a self-hosted/advanced override.

    Configure by setting:
        PRICE_PROVIDER_URL=https://your-provider.example.com/prices
    """

    def __init__(self, base_url: str, api_key: str | None = None) -> None:
        self.base_url = base_url
        self.api_key = api_key

    async def fetch_prices(
        self,
        isins: list[str],
        date: datetime.date,
    ) -> dict[str, Decimal]:
        import httpx

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # Only send ISINs + date — never holdings or portfolio data
        params = {"date": date.isoformat(), "isins": ",".join(isins)}

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(self.base_url, params=params, headers=headers)
            res.raise_for_status()
            data = res.json()

        return {isin: Decimal(str(price)) for isin, price in data.items()}


class YahooFinancePriceProvider(BasePriceProvider):
    """
    Unofficial Yahoo Finance price provider — free, no signup/API key.

    Yahoo has, since 2024, required a cookie + "crumb" handshake for its
    search/chart endpoints. These endpoints are undocumented and can change
    shape or add rate limits without notice, so every parsing step here is
    defensive: a failure for one ISIN never aborts the batch, it's simply
    omitted from the result.
    """

    _COOKIE_URL = "https://fc.yahoo.com"
    _CRUMB_URL = "https://query2.finance.yahoo.com/v1/test/getcrumb"
    _SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"
    _CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    _VALID_QUOTE_TYPES = {"EQUITY", "ETF", "MUTUALFUND", "INDEX"}
    # Yahoo's edge rate-limits/blocks the default httpx User-Agent (python-httpx/x.y)
    # almost immediately — a browser-like one is required, same as yfinance/Ghostfolio.
    _HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
    }

    async def _get_crumb(self, client) -> str | None:
        try:
            await client.get(self._COOKIE_URL, follow_redirects=True, timeout=10.0)
            res = await client.get(self._CRUMB_URL, timeout=10.0)
            res.raise_for_status()
            crumb = res.text.strip()
            if crumb and "<html" not in crumb.lower():
                return crumb
        except Exception:
            pass
        return None

    async def _search_quotes(self, query: str, client, crumb: str | None) -> list[dict]:
        params: dict[str, object] = {"q": query, "quotesCount": 8, "newsCount": 0}
        if crumb:
            params["crumb"] = crumb
        try:
            res = await client.get(self._SEARCH_URL, params=params, timeout=10.0)
            res.raise_for_status()
            data = res.json()
        except Exception:
            return []
        quotes = data.get("quotes") if isinstance(data, dict) else None
        if not quotes:
            return []
        return [
            q for q in quotes
            if isinstance(q, dict) and q.get("quoteType") in self._VALID_QUOTE_TYPES and q.get("symbol")
        ]

    async def _resolve_symbol(self, isin: str, client, crumb: str | None) -> dict | None:
        quotes = await self._search_quotes(isin, client, crumb)
        return quotes[0] if quotes else None

    async def _fetch_chart(
        self, symbol: str, client, crumb: str | None
    ) -> tuple[Decimal, str] | None:
        params: dict[str, object] = {"interval": "1d", "range": "5d"}
        if crumb:
            params["crumb"] = crumb
        try:
            res = await client.get(
                self._CHART_URL.format(symbol=symbol), params=params, timeout=10.0
            )
            res.raise_for_status()
            data = res.json()
        except Exception:
            return None
        try:
            result = data["chart"]["result"][0]
            meta = result.get("meta") or {}
            price = meta.get("regularMarketPrice")
            currency = meta.get("currency") or "USD"
            if price is None:
                closes = (result.get("indicators") or {}).get("quote", [{}])[0].get("close", [])
                closes = [c for c in closes if c is not None]
                price = closes[-1] if closes else None
            if price is None:
                return None
            return Decimal(str(price)), currency
        except (KeyError, IndexError, TypeError, ValueError):
            return None

    async def _fetch_chart_eur(
        self, symbol: str, client, crumb: str | None
    ) -> tuple[Decimal, str] | None:
        """Like `_fetch_chart`, but converts non-EUR quotes to EUR first.

        Every stored price/lot in this app is assumed to be EUR — but some
        Yahoo quotes for European insurance-wrapped fund share classes come
        back in a different trading currency than the EUR one on the
        account statement (e.g. a share class resolving to a JPY quote).
        Rather than threading currency through every market-value
        computation downstream, conversion happens once, here, using Yahoo's
        own FX-pair ticker convention (`"JPYEUR=X"` = value of 1 JPY in EUR).
        """
        chart = await self._fetch_chart(symbol, client, crumb)
        if chart is None:
            return None
        price, currency = chart
        if currency == "EUR":
            return price, currency
        fx = await self._fetch_chart(f"{currency}EUR=X", client, crumb)
        if fx is None:
            return None
        rate, _ = fx
        return price * rate, "EUR"

    async def fetch_prices(
        self,
        isins: list[str],
        date: datetime.date,
    ) -> dict[str, Decimal]:
        import httpx

        results: dict[str, Decimal] = {}
        semaphore = asyncio.Semaphore(4)

        async def _one(isin: str, client: httpx.AsyncClient, crumb: str | None) -> None:
            async with semaphore:
                try:
                    quote = await self._resolve_symbol(isin, client, crumb)
                    if not quote:
                        return
                    chart = await self._fetch_chart_eur(quote["symbol"], client, crumb)
                    if not chart:
                        return
                    price, _currency = chart
                    results[isin] = price
                except Exception:
                    return

        async with httpx.AsyncClient(headers=self._HEADERS) as client:
            crumb = await self._get_crumb(client)
            await asyncio.gather(*(_one(isin, client, crumb) for isin in isins))
        return results

    async def lookup(self, isin: str) -> InstrumentLookupResult | None:
        import httpx

        async with httpx.AsyncClient(headers=self._HEADERS) as client:
            crumb = await self._get_crumb(client)
            quote = await self._resolve_symbol(isin, client, crumb)
            if not quote:
                return None
            chart = await self._fetch_chart_eur(quote["symbol"], client, crumb)
            if not chart:
                return None
            price, currency = chart
            symbol = quote["symbol"]
            name = quote.get("shortname") or quote.get("longname") or symbol
            return InstrumentLookupResult(
                isin=isin,
                symbol=symbol,
                name=name,
                ticker=symbol,
                currency=currency,
                price=price,
                price_date=datetime.date.today(),
                asset_class=_guess_asset_class(quote),
            )

    async def search(self, query: str) -> list[InstrumentSearchResult]:
        import httpx

        results: list[InstrumentSearchResult] = []
        semaphore = asyncio.Semaphore(4)

        async def _one(quote: dict, client: httpx.AsyncClient, crumb: str | None) -> None:
            async with semaphore:
                chart = await self._fetch_chart_eur(quote["symbol"], client, crumb)
                if not chart:
                    return
                price, currency = chart
                results.append(InstrumentSearchResult(
                    symbol=quote["symbol"],
                    name=quote.get("shortname") or quote.get("longname") or quote["symbol"],
                    currency=currency,
                    price=price,
                    price_date=datetime.date.today(),
                    asset_class=_guess_asset_class(quote),
                ))

        async with httpx.AsyncClient(headers=self._HEADERS) as client:
            crumb = await self._get_crumb(client)
            quotes = await self._search_quotes(query, client, crumb)
            await asyncio.gather(*(_one(q, client, crumb) for q in quotes))
        return results

    async def fetch_price_by_symbol(self, symbol: str) -> Decimal | None:
        import httpx

        async with httpx.AsyncClient(headers=self._HEADERS) as client:
            crumb = await self._get_crumb(client)
            chart = await self._fetch_chart_eur(symbol, client, crumb)
            return chart[0] if chart else None


async def get_price_provider(session: AsyncSession) -> BasePriceProvider | None:
    """Return the configured price provider, or None if disabled (default)."""
    settings = get_settings()
    if settings.price_provider_url:
        return HttpPriceProvider(
            base_url=settings.price_provider_url,
            api_key=None,  # TODO: load from secret file if configured
        )

    from app.domains.accounts.repository import PersonRepository

    household = await PersonRepository(session).get_household()
    if household is not None and household.price_lookup_enabled:
        return YahooFinancePriceProvider()
    return None
