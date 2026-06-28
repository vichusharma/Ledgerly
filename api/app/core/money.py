"""Money utilities — all arithmetic uses Decimal, never float."""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
FOUR_DP = Decimal("0.0001")


def round_currency(amount: Decimal, places: int = 2) -> Decimal:
    """Round to `places` decimal places using banker-safe ROUND_HALF_UP."""
    quantize_to = Decimal(10) ** -places
    return amount.quantize(quantize_to, rounding=ROUND_HALF_UP)


def to_decimal(value: float | int | str | Decimal) -> Decimal:
    """Convert any numeric-ish type to Decimal safely."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def pct(numerator: Decimal, denominator: Decimal) -> Decimal:
    """Return percentage (0–100) or 0 if denominator is zero."""
    if denominator == Decimal("0"):
        return Decimal("0")
    return round_currency((numerator / denominator) * Decimal("100"), 4)
