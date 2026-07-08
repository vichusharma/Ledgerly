"""
Feature J4 (docs/Backlog.md) — mapping Epic I's tax estimate plus Epic
J's filing-specific facts (foreign income, foreign accounts) onto
DGFiP form line items (2042/2047/3916), without duplicating
`core/tax.py`'s bracket/quotient-familial math.

Pure, stateless functions: no DB, no network. Callers pass in the same
`BaremeBracket` list and quotient-familial facts (`parts`, `base_parts`,
`plafond_per_half_part`) already resolved by `TaxService`/`core/tax.py`.

Documented simplifications (see docs/Backlog.md):
- Box codes mapped below are representative, not verified against the
  actual current-year DGFiP instructions — must be checked before ever
  being used for a real filing (same caveat as every generated PDF).
- `TreatyMetadata` is seeded for a handful of countries only; any other
  country falls back to the credit method, flagged via
  `treaty_method_defaulted_unseeded_country`.
- The credit-method and effective-rate computations both approximate a
  real per-income-category treaty analysis as one marginal-tax-slice
  calculation — real treaties can carve out different treatment per
  income type (dividends vs. salary vs. capital gains) within the same
  country, which isn't modeled here.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.core.tax import BaremeBracket, compute_quotient_tax

CREDIT_METHOD = "credit_equal_to_french_tax"
EFFECTIVE_RATE_METHOD = "exemption_with_effective_rate"


def compute_french_tax_attributable_to_income(
    total_taxable_income: Decimal,
    foreign_income_slice: Decimal,
    parts: Decimal,
    base_parts: Decimal,
    brackets: list[BaremeBracket],
    plafond_per_half_part: Decimal,
) -> Decimal:
    """"Crédit d'impôt égal à l'impôt français" — the French tax that
    would be due on the foreign income slice alone, computed as the
    marginal difference tax(total) - tax(total - slice) at the same
    parts/brackets. This is the amount of French tax creditable against
    the (assumed, not separately modeled) foreign tax already paid —
    naturally capped at the slice's own marginal contribution.
    """
    if foreign_income_slice <= 0:
        return Decimal("0")
    tax_with_income, _ = compute_quotient_tax(
        total_taxable_income, parts, base_parts, brackets, plafond_per_half_part
    )
    tax_without_income, _ = compute_quotient_tax(
        max(total_taxable_income - foreign_income_slice, Decimal("0")),
        parts, base_parts, brackets, plafond_per_half_part,
    )
    return tax_with_income - tax_without_income


def compute_effective_rate_exemption(
    total_taxable_income: Decimal,
    foreign_income_slice: Decimal,
    parts: Decimal,
    base_parts: Decimal,
    brackets: list[BaremeBracket],
    plafond_per_half_part: Decimal,
) -> tuple[Decimal, Decimal]:
    """"Exemption avec taux effectif" — foreign income is excluded from
    French tax itself, but raises the average ("effective") rate applied
    to the remaining French-source income. Returns
    (effective_rate, french_tax_due) where `french_tax_due` is the tax
    on French-source income only, computed at the rate implied by total
    (worldwide) income.
    """
    if total_taxable_income <= 0:
        return (Decimal("0"), Decimal("0"))
    tax_on_worldwide, _ = compute_quotient_tax(
        total_taxable_income, parts, base_parts, brackets, plafond_per_half_part
    )
    effective_rate = tax_on_worldwide / total_taxable_income
    french_source_income = max(total_taxable_income - foreign_income_slice, Decimal("0"))
    french_tax_due = (effective_rate * french_source_income).quantize(Decimal("0.01"))
    return (effective_rate.quantize(Decimal("0.0001")), french_tax_due)


def resolve_elimination_method(
    line_override: str | None,
    treaty_default: str | None,
) -> tuple[str, list[str]]:
    """Per-line resolution order (Feature J4-S3): an explicit override on
    the `ForeignIncomeDeclaration` line wins; otherwise the country's
    `TreatyMetadata` default; otherwise fall back to the credit method
    and flag it, since an unseeded country has no known treaty default.
    """
    if line_override:
        return (line_override, [])
    if treaty_default:
        return (treaty_default, [])
    return (CREDIT_METHOD, ["treaty_method_defaulted_unseeded_country"])


@dataclass(frozen=True)
class BoxEntry:
    code: str
    label: str
    amount: Decimal


def map_estimate_to_2042_boxes(salaries_by_declarant: list[Decimal]) -> list[BoxEntry]:
    """Form 2042 salary boxes — 1AJ for declarant 1, 1BJ for declarant 2
    (the household's own two returns, `married_pacs` filing). A `single`
    filer or a household with only one salaried adult gets just 1AJ.
    """
    codes = ("1AJ", "1BJ")
    return [
        BoxEntry(code=codes[i], label=f"Traitements et salaires (déclarant {i + 1})", amount=amt)
        for i, amt in enumerate(salaries_by_declarant[:2])
        if amt > 0
    ]


def map_investment_income_to_2042_boxes(
    dividends: Decimal, pfu_chosen: bool
) -> list[BoxEntry]:
    """Form 2042 investment-income boxes — 2DC (dividends eligible for
    the 40% abattement, only relevant if barème is chosen over PFU) and
    2CK (PFU-taxed dividends, box used when the flat-tax option applies).
    Realized capital gains use 3VG on Form 2042-C, not mapped here since
    Epic J's engine doesn't yet split gains from dividends at box level.
    """
    if dividends <= 0:
        return []
    code = "2CK" if pfu_chosen else "2DC"
    label = (
        "Revenus des valeurs mobilières (PFU)" if pfu_chosen
        else "Revenus des valeurs mobilières (barème, abattement 40%)"
    )
    return [BoxEntry(code=code, label=label, amount=dividends)]


@dataclass(frozen=True)
class ForeignIncomeLine2047:
    source_country_code: str
    source_description: str
    gross_amount_eur: Decimal
    elimination_method: str
    simplification_keys: list[str]
    french_tax_credit_or_exemption: Decimal


def map_foreign_income_to_2047_lines(
    declarations: list[dict],
    treaty_defaults: dict[str, str],
    total_taxable_income: Decimal,
    parts: Decimal,
    base_parts: Decimal,
    brackets: list[BaremeBracket],
    plafond_per_half_part: Decimal,
) -> list[ForeignIncomeLine2047]:
    """One Form 2047 line per `ForeignIncomeDeclaration`. Each
    declaration dict is expected to have `source_country_code`,
    `source_description`, `gross_amount_eur`, and
    `elimination_method_override` (may be None).
    """
    lines: list[ForeignIncomeLine2047] = []
    for d in declarations:
        method, keys = resolve_elimination_method(
            d.get("elimination_method_override"),
            treaty_defaults.get(d["source_country_code"]),
        )
        gross = d["gross_amount_eur"]
        if method == EFFECTIVE_RATE_METHOD:
            _, french_tax_due = compute_effective_rate_exemption(
                total_taxable_income, gross, parts, base_parts, brackets, plafond_per_half_part
            )
            amount = french_tax_due
        else:
            amount = compute_french_tax_attributable_to_income(
                total_taxable_income, gross, parts, base_parts, brackets, plafond_per_half_part
            )
        lines.append(ForeignIncomeLine2047(
            source_country_code=d["source_country_code"],
            source_description=d["source_description"],
            gross_amount_eur=gross,
            elimination_method=method,
            simplification_keys=keys,
            french_tax_credit_or_exemption=amount,
        ))
    return lines


@dataclass(frozen=True)
class ForeignAccountEntry3916:
    bank_name: str
    country_code: str
    account_identifier_masked: str | None
    opened_this_year: bool
    closed_this_year: bool


def map_foreign_accounts_to_3916_entries(
    declarations: list[dict],
) -> list[ForeignAccountEntry3916]:
    """One Form 3916 entry per `ForeignAccountDeclaration`."""
    return [
        ForeignAccountEntry3916(
            bank_name=d["bank_name"],
            country_code=d["country_code"],
            account_identifier_masked=d.get("account_identifier_masked"),
            opened_this_year=bool(d.get("opened_this_year")),
            closed_this_year=bool(d.get("closed_this_year")),
        )
        for d in declarations
    ]


def validate_filing_inputs(
    *,
    has_residency: bool,
    foreign_income_countries: set[str],
    declared_foreign_account_countries: set[str],
    declarations_missing_documents: list[str],
) -> list[str]:
    """Pre-flight validation (Feature J4-S6) — returns a list of
    human-readable issue strings, not an exception; the caller decides
    whether to block computation or just warn.
    """
    issues: list[str] = []
    if not has_residency:
        issues.append("missing_residency_profile")
    undeclared = foreign_income_countries - declared_foreign_account_countries
    for country in sorted(undeclared):
        issues.append(f"foreign_income_from_{country}_with_no_declared_account")
    for label in declarations_missing_documents:
        issues.append(f"no_source_document_for_{label}")
    return issues
