"""
Asset allocation computation — pure function.

Given a dict of {asset_class: market_value} and a dict of {asset_class: target_pct},
returns the actual percentages, target percentages, and drift for each class.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class AllocationSlice:
    asset_class: str
    market_value: Decimal
    actual_pct: Decimal
    target_pct: Decimal
    drift_pct: Decimal  # actual - target


def compute_allocation(
    holdings: dict[str, Decimal],       # {asset_class: market_value}
    targets: dict[str, Decimal],        # {asset_class: target_pct (0–100)}
) -> list[AllocationSlice]:
    """
    Compute current allocation and drift vs. target.

    Args:
        holdings: Market value per asset class (EUR).
        targets: Target percentage per asset class (sums to 100).

    Returns:
        List of AllocationSlice, one per asset class present in either dict.
    """
    total = sum(holdings.values(), Decimal("0"))
    all_classes = set(holdings.keys()) | set(targets.keys())
    slices: list[AllocationSlice] = []

    for cls in sorted(all_classes):
        mv = holdings.get(cls, Decimal("0"))
        actual_pct = (mv / total * Decimal("100")).quantize(Decimal("0.01")) if total else Decimal("0")
        target_pct = targets.get(cls, Decimal("0"))
        drift = (actual_pct - target_pct).quantize(Decimal("0.01"))
        slices.append(AllocationSlice(
            asset_class=cls,
            market_value=mv,
            actual_pct=actual_pct,
            target_pct=target_pct,
            drift_pct=drift,
        ))

    return slices
