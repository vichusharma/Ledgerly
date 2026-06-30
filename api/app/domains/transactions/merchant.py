"""Best-effort merchant extraction from free-text bank descriptions.

French bank statements have no structured merchant field — the shop name is
buried in card/operation noise like ``CB CARREFOUR MARKET 12/05 PARIS``. This
module strips that noise to a stable merchant key so spending can be grouped by
place. It is heuristic and approximate by design (the user accepted this
trade-off): two descriptions for the same shop should collapse to one merchant,
even if the result is occasionally imperfect.
"""
from __future__ import annotations

import re

# Leading operation prefixes (longest first so "PAIEMENT CB" wins over "CB").
_PREFIXES = [
    "paiement par carte", "paiement carte", "paiement cb", "achat cb",
    "retrait cb", "retrait dab", "prelevement", "prlv sepa", "prlv",
    "virement", "vir sepa", "vir inst", "vir", "carte", "cb",
    "facture", "echeance", "remise cheque", "cheque",
]
_PREFIX_RE = re.compile(
    r"^(?:" + "|".join(re.escape(p) for p in _PREFIXES) + r")\b[\s:*-]*",
    re.IGNORECASE,
)

# Trailing/embedded dates: 12/05, 12.05.26, 12-05-2026, 2026-05-12.
_DATE_RE = re.compile(
    r"\b\d{1,2}[/.\-]\d{1,2}(?:[/.\-]\d{2,4})?\b"
    r"|\b\d{4}[/.\-]\d{1,2}[/.\-]\d{1,2}\b",
)
# Long digit runs (card refs / transaction ids).
_DIGITRUN_RE = re.compile(r"\b\d{5,}\b")

# Trailing tokens that are place/legal noise rather than the merchant name.
_CITIES = {
    "paris", "lyon", "marseille", "toulouse", "bordeaux", "lille", "nantes",
    "nice", "strasbourg", "montpellier", "rennes", "reims", "grenoble", "dijon",
    "angers", "nimes", "villeurbanne", "clermont", "tours", "amiens", "metz",
    "perpignan", "besancon", "orleans", "mulhouse", "caen", "nancy", "rouen",
    "roubaix", "tourcoing", "cergy", "versailles", "courbevoie", "nanterre",
    "boulogne", "argenteuil", "montreuil", "creteil", "aix", "antibes",
}
_COUNTRY = {"fr", "france"}
_CORP = {"sarl", "sas", "sa", "eurl", "sasu", "sci", "snc"}
_DROP_TRAILING = _CITIES | _COUNTRY | _CORP

_SPLIT_RE = re.compile(r"[\s,*/]+")


def _cap(token: str) -> str:
    """Capitalize, but keep 3–4 letter all-caps acronyms (SNCF, FNAC, EDF)."""
    if token.isupper() and token.isalpha() and 3 <= len(token) <= 4:
        return token
    return token.capitalize()


def normalize_merchant(description: str) -> str:
    """Reduce a raw bank description to a stable, human-readable merchant name.

    Falls back to the trimmed/title-cased original if cleanup empties it.
    """
    if not description or not description.strip():
        return "—"
    original = description.strip()

    s = _PREFIX_RE.sub("", original)
    s = _DATE_RE.sub(" ", s)
    s = _DIGITRUN_RE.sub(" ", s)

    tokens = [t for t in _SPLIT_RE.split(s) if t]
    # Drop leading pure-number tokens (e.g. a card fragment after the prefix).
    while tokens and tokens[0].isdigit():
        tokens.pop(0)
    # Drop trailing place/legal/number noise, but keep at least one token.
    while len(tokens) > 1 and (
        tokens[-1].isdigit() or tokens[-1].lower() in _DROP_TRAILING
    ):
        tokens.pop()

    if not tokens:
        return original.title()
    return " ".join(_cap(t) for t in tokens)
