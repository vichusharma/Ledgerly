"""
French tax-wrapper rules engine (Phase 3).

Provides hints about key wrapper milestones:
- PEA: 5-year clock for tax-free withdrawal eligibility
- Assurance Vie: 8-year threshold for enhanced tax treatment
- PER: deductibility hint for contributions
- PERCO/PEE: employer match + blocking periods

Pure: takes account + date, returns hints. No DB, no network.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class TaxHint:
    wrapper_type: str
    key: str
    message: str
    eligible: bool | None  # None = N/A
    eligible_date: datetime.date | None


def get_wrapper_hints(
    wrapper_type: str,
    account_open_date: datetime.date,
    current_date: datetime.date | None = None,
) -> list[TaxHint]:
    """
    Return tax hints for a given wrapper and its opening date.

    Args:
        wrapper_type: One of PEA, PEA_PME, AV, PER, PERCO, PEE, etc.
        account_open_date: Date the account was opened.
        current_date: Date for calculation (default: today).

    Returns:
        List of TaxHint objects — each is a human-readable hint.
    """
    if current_date is None:
        current_date = datetime.date.today()

    hints: list[TaxHint] = []

    if wrapper_type in ("PEA", "PEA_PME"):
        # 5-year holding period for tax-free capital gains
        five_year = account_open_date.replace(year=account_open_date.year + 5)
        eligible = current_date >= five_year
        hints.append(TaxHint(
            wrapper_type=wrapper_type,
            key="five_year_clock",
            message=(
                f"Votre {wrapper_type} a plus de 5 ans — les retraits sont exonérés d'impôt sur les plus-values."
                if eligible
                else f"Votre {wrapper_type} sera éligible aux retraits exonérés le {five_year.strftime('%d/%m/%Y')}."
            ),
            eligible=eligible,
            eligible_date=five_year,
        ))

    elif wrapper_type == "AV":
        # 8-year threshold for enhanced tax allowance (4600€/9200€ abattement)
        eight_year = account_open_date.replace(year=account_open_date.year + 8)
        eligible = current_date >= eight_year
        hints.append(TaxHint(
            wrapper_type=wrapper_type,
            key="eight_year_threshold",
            message=(
                "Votre Assurance Vie a plus de 8 ans — abattement annuel de 4 600 € (célibataire) ou 9 200 € (couple) applicable."
                if eligible
                else f"Votre AV atteindra les 8 ans le {eight_year.strftime('%d/%m/%Y')}."
            ),
            eligible=eligible,
            eligible_date=eight_year,
        ))

    elif wrapper_type in ("PER", "PERO"):
        hints.append(TaxHint(
            wrapper_type=wrapper_type,
            key="deductibility",
            message="Les versements sur votre PER sont déductibles de votre revenu imposable dans la limite du plafond épargne retraite.",
            eligible=True,
            eligible_date=None,
        ))
        hints.append(TaxHint(
            wrapper_type=wrapper_type,
            key="blocking",
            message="Les sommes sont bloquées jusqu'à la retraite (sauf cas de déblocage anticipé : achat résidence principale, invalidité, décès du conjoint, etc.).",
            eligible=None,
            eligible_date=None,
        ))

    elif wrapper_type in ("PERCO", "PEE"):
        lock_years = 5 if wrapper_type == "PEE" else 0  # PERCO locks until retirement
        if wrapper_type == "PEE":
            unlock_date = account_open_date.replace(year=account_open_date.year + 5)
            eligible = current_date >= unlock_date
            hints.append(TaxHint(
                wrapper_type=wrapper_type,
                key="pee_lock",
                message=(
                    "PEE débloqué — vous pouvez retirer les sommes en franchise d'impôt."
                    if eligible
                    else f"PEE : fonds bloqués 5 ans jusqu'au {unlock_date.strftime('%d/%m/%Y')} (sauf cas de déblocage anticipé)."
                ),
                eligible=eligible,
                eligible_date=unlock_date,
            ))

    return hints
