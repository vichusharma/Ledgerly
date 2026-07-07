"""
French income-tax engine — barème progressif, quotient familial, régime des
impatriés, YTD withholding reconciliation (Feature I3), and realized
investment income — capital gains, dividends, wrapper exemptions,
PFU-vs-barème (Feature I4) — of docs/Backlog.md.

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
- Realized gains use average-cost accounting (not FIFO/LIFO tax-lot
  matching), consistent with InvestmentService._compute_positions.
- Wrapper exemptions (PEA 5yr / AV 8yr) are the only ones modeled; other
  wrappers (CTO, PER, etc.) get no exemption. Eligibility is evaluated
  once as of the tax year's Dec 31, not per individual lot date.
- AV taxation is modeled as "realized on sell," not "realized on
  withdrawal (rachat)" — real French law only taxes AV gains when cash
  actually leaves the contract, not on internal fund arbitrage. This may
  overstate tax for AV holders who switch funds without withdrawing.
- The 17.2% social-charges (prélèvements sociaux) component of PFU is not
  modeled — only the 12.8% income-tax component.
- The PFU-vs-barème "option globale" election is a real household-wide
  annual choice; this engine approximates it as one household-level (or,
  for single filers, primary-person-level) comparison rather than a
  legally-precise per-instrument election.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.infra.tax_rules import get_wrapper_hints


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


def compute_parts(
    filing_status: str, num_minor_dependents: int, num_adult_dependents: int = 0
) -> Decimal:
    """Quotient familial parts: 1 (single) or 2 (married/pacs) base.

    Minor dependents follow the standard progressive rule: +0.5 for each of
    the first 2, +1 for each additional one beyond that. Adult dependents
    (e.g. an ascendant living in the household, or an adult child not
    treated as a minor) each add a flat +1 full part instead, outside that
    progression — a documented simplification (see
    "adult_dependents_flat_one_part" in docs/Backlog.md) that doesn't model
    the real election between rattachement-as-a-child vs. a fixed income
    deduction for attached adult children.
    """
    base = Decimal("2") if filing_status == "married_pacs" else Decimal("1")
    if num_minor_dependents <= 0:
        minor_parts = Decimal("0")
    elif num_minor_dependents <= 2:
        minor_parts = Decimal("0.5") * num_minor_dependents
    else:
        minor_parts = Decimal("1") + Decimal(num_minor_dependents - 2)
    adult_parts = Decimal(max(0, num_adult_dependents))
    return base + minor_parts + adult_parts


def is_minor_dependent(date_of_birth: datetime.date | None, as_of: datetime.date) -> bool:
    """Whether a dependent counts as a minor child for quotient-familial
    purposes, as of Dec 31 of the tax year (the standard French reference
    date). A dependent with no known birth date is conservatively treated
    as a minor (the more common case, and the one that doesn't require the
    flat-adult-part disclaimer) — callers should flag this via a
    simplification key when it happens, since it's a guess, not a fact."""
    if date_of_birth is None:
        return True
    age = as_of.year - date_of_birth.year - (
        (as_of.month, as_of.day) < (date_of_birth.month, date_of_birth.day)
    )
    return age < 18


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


# ── Feature I4: realized capital gains, dividends, wrapper exemptions ──────


@dataclass(frozen=True)
class LotEvent:
    """Minimal lot data needed for realized-gain/dividend math — decoupled
    from the ORM (InvestmentLot) so this module stays DB-free. `lot_type`
    is one of "buy"/"sell"/"dividend"."""
    lot_type: str
    quantity: Decimal
    price: Decimal
    fees: Decimal
    settled_at: datetime.date


def compute_realized_gains_for_year(events: list[LotEvent], year: int) -> Decimal:
    """Realized capital gain/loss for `sell` events settled in `year`, using
    average-cost accounting (average cost per unit across all prior buys,
    same convention as InvestmentService._compute_positions — not FIFO/LIFO
    tax-lot matching).

    `events` must be pre-filtered to a single (account, instrument) position
    and include the FULL lot history up to and including `year` (not just
    `year` itself), since the average cost basis at time of sale depends on
    every prior buy, not just the ones that happen to fall in `year`.
    """
    ordered = sorted(events, key=lambda e: e.settled_at)
    running_qty = Decimal("0")
    running_cost = Decimal("0")
    gain_in_year = Decimal("0")
    for e in ordered:
        if e.lot_type == "buy":
            running_qty += e.quantity
            running_cost += e.quantity * e.price + e.fees
        elif e.lot_type == "sell":
            avg_cost = running_cost / running_qty if running_qty else Decimal("0")
            sold_qty = min(e.quantity, running_qty)
            cost_of_sold = avg_cost * sold_qty
            proceeds = e.quantity * e.price - e.fees
            if e.settled_at.year == year:
                gain_in_year += proceeds - cost_of_sold
            running_qty -= sold_qty
            running_cost -= cost_of_sold
    return gain_in_year


def sum_dividends_for_year(events: list[LotEvent], year: int) -> Decimal:
    """Sum dividend-lot amounts settled in `year`. Dividend lots store the
    cash amount in `price` (quantity isn't meaningful for this lot type),
    matching InvestmentService.get_performance's existing convention."""
    return sum(
        (e.price for e in events if e.lot_type == "dividend" and e.settled_at.year == year),
        Decimal("0"),
    )


@dataclass(frozen=True)
class WrapperGain:
    """One account's realized-gain-plus-dividend total for the year, tagged
    with the wrapper facts needed to decide exemption eligibility."""
    wrapper_type: str | None
    account_open_date: datetime.date | None
    gain: Decimal


def apply_wrapper_exemptions(
    wrapper_gains: list[WrapperGain],
    filing_status: str,
    as_of: datetime.date,
) -> tuple[Decimal, list[str]]:
    """Zero out PEA/PEA_PME gains past the 5-year clock and apply the AV
    8-year abattement (4,600 EUR single / 9,200 EUR married-pacs, applied
    once at household level across all AV accounts pooled together, not
    per-account) — via the existing `get_wrapper_hints` rules engine, not
    duplicated math. Other wrappers (CTO, PER, etc.) get no exemption
    modeled. Losses (negative gain) are never exempted — they flow straight
    into the taxable total, reducing it.

    Returns (taxable_investment_income, simplification_keys_applied).
    """
    taxable = Decimal("0")
    av_pool = Decimal("0")
    keys: set[str] = set()

    for wg in wrapper_gains:
        if wg.wrapper_type is None or wg.account_open_date is None or wg.gain <= 0:
            taxable += wg.gain
            continue

        if wg.wrapper_type in ("PEA", "PEA_PME"):
            hints = get_wrapper_hints(wg.wrapper_type, wg.account_open_date, as_of)
            eligible = any(h.key == "five_year_clock" and h.eligible for h in hints)
            if eligible:
                keys.add("pea_five_year_exemption")
            else:
                taxable += wg.gain
        elif wg.wrapper_type == "AV":
            hints = get_wrapper_hints(wg.wrapper_type, wg.account_open_date, as_of)
            eligible = any(h.key == "eight_year_threshold" and h.eligible for h in hints)
            if eligible:
                av_pool += wg.gain
                keys.add("av_eight_year_abattement")
            else:
                taxable += wg.gain
        else:
            taxable += wg.gain

    if av_pool > 0:
        abattement = Decimal("9200") if filing_status == "married_pacs" else Decimal("4600")
        taxable += max(Decimal("0"), av_pool - abattement)

    return taxable, sorted(keys)


def compute_pfu(investment_income: Decimal) -> Decimal:
    """PFU ("flat tax") income-tax component only (12.8%) — the 17.2%
    social-charges component isn't modeled (see the module-level
    "social_charges_not_modeled" simplification)."""
    if investment_income <= 0:
        return Decimal("0")
    return _r2(investment_income * Decimal("0.128"))


def compare_pfu_vs_bareme(
    salary_taxable_income: Decimal,
    investment_income: Decimal,
    parts: Decimal,
    base_parts: Decimal,
    brackets: list[BaremeBracket],
    plafond_per_half_part: Decimal,
) -> tuple[str, Decimal, Decimal]:
    """Compare electing the PFU flat tax against opting into the barème for
    ALL investment income (the real "option globale" — a household-wide
    annual election that must apply uniformly, approximated here as one
    comparison rather than a per-instrument choice).

    Returns (chosen, pfu_total_tax, bareme_total_tax) where both totals are
    salary tax + investment tax combined, so they're directly comparable;
    `chosen` is whichever is lower ("pfu" on a tie, since PFU has no extra
    filing complexity in reality).
    """
    salary_tax, _ = compute_quotient_tax(
        salary_taxable_income, parts, base_parts, brackets, plafond_per_half_part
    )
    if investment_income <= 0:
        return ("pfu", salary_tax, salary_tax)

    pfu_total_tax = salary_tax + compute_pfu(investment_income)
    combined_income = salary_taxable_income + investment_income
    bareme_total_tax, _ = compute_quotient_tax(
        combined_income, parts, base_parts, brackets, plafond_per_half_part
    )

    chosen = "pfu" if pfu_total_tax <= bareme_total_tax else "bareme"
    return (chosen, pfu_total_tax, bareme_total_tax)
