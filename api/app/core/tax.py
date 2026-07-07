"""
French income-tax engine — barème progressif, quotient familial, régime des
impatriés, YTD withholding reconciliation (Feature I3 of docs/Backlog.md).

Pure, stateless functions: no DB, no network. Brackets are passed in
(sourced from the `tax_year_configs` table by the caller) rather than
hardcoded here, since the barème changes every year via Loi de Finances.

Documented simplifications (see docs/Backlog.md):
- Quotient familial plafonnement: general case only, not the higher caps
  for single parents/widowed/disabled taxpayers.
- Only the flat-30% impatriate election is computed; "specific premium"
  is recognized but not computed (flagged instead).
- YTD-to-annual projection is linear (ytd / months_elapsed * 12), ignoring
  bonus/raise timing within the year.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


@dataclass(frozen=True)
class BaremeBracket:
    """One tranche of the barème progressif. `up_to=None` means no upper bound."""
    up_to: Decimal | None
    rate: Decimal


def _r2(d: Decimal) -> Decimal:
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def apply_bareme(income: Decimal, brackets: list[BaremeBracket]) -> Decimal:
    """Progressive tax on `income` given ascending brackets (last `up_to=None`).

    Returns the unrounded tax — callers round once at the point where a
    final figure is produced, to avoid compounding rounding error across
    intermediate steps (e.g. quotient familial's per-part/×parts math).
    """
    if income <= 0:
        return Decimal("0")
    tax = Decimal("0")
    lower = Decimal("0")
    for bracket in brackets:
        upper = income if bracket.up_to is None else min(bracket.up_to, income)
        if upper > lower:
            tax += (upper - lower) * bracket.rate
        lower = income if bracket.up_to is None else bracket.up_to
        if lower >= income:
            break
    return tax


def compute_parts(filing_status: str, num_dependents: int) -> Decimal:
    """Quotient familial parts: 1 (single) or 2 (married/pacs) base, +0.5 for
    each of the first 2 dependents, +1 for each additional dependent."""
    base = Decimal("2") if filing_status == "married_pacs" else Decimal("1")
    if num_dependents <= 0:
        return base
    if num_dependents <= 2:
        return base + Decimal("0.5") * num_dependents
    return base + Decimal("1") + Decimal(num_dependents - 2)


def compute_quotient_tax(
    taxable_income: Decimal,
    parts: Decimal,
    base_parts: Decimal,
    brackets: list[BaremeBracket],
    plafond_per_half_part: Decimal,
) -> tuple[Decimal, bool]:
    """Tax after the quotient familial mechanism, with the general-case
    plafonnement cap on the advantage gained from parts above `base_parts`
    (i.e. the parts contributed by dependents, not by marital status).

    Returns (tax, plafonnement_applied).
    """
    if parts <= 0:
        parts = Decimal("1")
    tax_at_parts = apply_bareme(taxable_income / parts, brackets) * parts

    if parts <= base_parts:
        return (_r2(tax_at_parts), False)

    tax_at_base = apply_bareme(taxable_income / base_parts, brackets) * base_parts
    extra_half_parts = (parts - base_parts) / Decimal("0.5")
    max_reduction = extra_half_parts * plafond_per_half_part
    actual_reduction = tax_at_base - tax_at_parts

    if actual_reduction > max_reduction:
        return (_r2(tax_at_base - max_reduction), True)
    return (_r2(tax_at_parts), False)


def apply_impatriate_exemption(
    taxable_income: Decimal, enabled: bool, method: str | None
) -> tuple[Decimal, bool]:
    """Flat-30% impatriate exemption (Art. 155 B CGI). Only `flat_30` is
    computed — `specific_premium` is left unchanged and flagged False so
    the caller can surface a "not computed" disclaimer."""
    if not enabled or method != "flat_30":
        return (taxable_income, False)
    return (taxable_income - taxable_income * Decimal("0.30"), True)


def impatriate_years_remaining(arrival_date: datetime.date, as_of: datetime.date) -> int:
    """Years remaining in the 8-year impatriate window (inclusive of the
    arrival year), clamped to 0 once expired."""
    eligible_through_year = arrival_date.year + 7
    return max(0, eligible_through_year - as_of.year)


def project_annual_from_ytd(ytd_amount: Decimal, as_of_month: int) -> Decimal:
    """Linear extrapolation of a year-to-date figure to a full-year estimate."""
    if as_of_month <= 0:
        return Decimal("0")
    return (ytd_amount / as_of_month) * 12


def reconcile_withholding(estimated_tax: Decimal, pas_withheld_projected: Decimal) -> Decimal:
    """Balance vs. withholding already deducted at source: positive = owe
    more, negative = refund."""
    return estimated_tax - pas_withheld_projected
