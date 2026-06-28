"""
Pluggable price provider interface (Phase 3).

Disabled by default. When enabled:
- Only fetches PRICES — never sends holdings, ISIN lists, or any user data
- The settings.price_provider_url must be set explicitly
- Implement a concrete provider by subclassing BasePriceProvider

Usage:
    provider = get_price_provider()
    if provider:
        prices = await provider.fetch_prices(["IE00B4L5Y983"], date.today())
"""
from __future__ import annotations

import datetime
from abc import ABC, abstractmethod
from decimal import Decimal

from app.infra.settings import get_settings


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

        IMPORTANT: This method MUST NOT include any user data (portfolio holdings,
        quantities, account identifiers) in the outbound request.
        """
        ...


class HttpPriceProvider(BasePriceProvider):
    """
    Generic HTTP price provider stub.

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


def get_price_provider() -> BasePriceProvider | None:
    """Return the configured price provider, or None if disabled (default)."""
    settings = get_settings()
    if not settings.price_provider_url:
        return None
    return HttpPriceProvider(
        base_url=settings.price_provider_url,
        api_key=None,  # TODO: load from secret file if configured
    )
