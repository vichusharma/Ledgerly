"""Built-in CSV layout presets for major French banks.

Keyed by a lowercase institution substring (matched against the account's
``institution``). A preset fixes the reliable, bank-specific knobs — delimiter,
decimal separator, date format — and offers best-guess column names. Column
names are only applied when they actually appear in the file's headers; any
that don't match fall back to keyword auto-detection, so a slightly stale
preset can never make an import worse.

Layouts are best-effort from real exports and may drift as banks change their
formats; the manual mapping step remains the safety net.
"""
from __future__ import annotations

# Each value: {column_map, date_format, decimal_separator, delimiter}
# column_map keys mirror csv_parser.detect_columns(): date/amount/debit/credit/description
BANK_PRESETS: dict[str, dict] = {
    "boursorama": {
        "column_map": {"date": "dateOp", "amount": "amount", "description": "label"},
        "date_format": "%Y-%m-%d",
        "decimal_separator": ",",
        "delimiter": ";",
    },
    "fortuneo": {
        "column_map": {"date": "Date", "amount": "Montant", "description": "Libellé"},
        "date_format": "%d/%m/%Y",
        "decimal_separator": ",",
        "delimiter": ";",
    },
    "crédit agricole": {
        "column_map": {
            "date": "Date", "debit": "Débit euros",
            "credit": "Crédit euros", "description": "Libellé",
        },
        "date_format": "%d/%m/%Y",
        "decimal_separator": ",",
        "delimiter": ";",
    },
    "bnp paribas": {
        "column_map": {"date": "Date opération", "amount": "Montant", "description": "Libellé"},
        "date_format": "%d/%m/%Y",
        "decimal_separator": ",",
        "delimiter": ";",
    },
    "lcl": {
        "column_map": {"date": "Date", "amount": "Montant", "description": "Libellé"},
        "date_format": "%d/%m/%Y",
        "decimal_separator": ",",
        "delimiter": ";",
    },
    "société générale": {
        "column_map": {"date": "Date", "amount": "Montant", "description": "Libellé"},
        "date_format": "%d/%m/%Y",
        "decimal_separator": ",",
        "delimiter": ";",
    },
    "caisse d'épargne": {
        "column_map": {
            "date": "Date", "debit": "Débit", "credit": "Crédit", "description": "Libellé",
        },
        "date_format": "%d/%m/%Y",
        "decimal_separator": ",",
        "delimiter": ";",
    },
    "banque populaire": {
        "column_map": {
            "date": "Date", "debit": "Débit", "credit": "Crédit", "description": "Libellé",
        },
        "date_format": "%d/%m/%Y",
        "decimal_separator": ",",
        "delimiter": ";",
    },
    "hello bank": {
        "column_map": {"date": "Date opération", "amount": "Montant", "description": "Libellé"},
        "date_format": "%d/%m/%Y",
        "decimal_separator": ",",
        "delimiter": ";",
    },
}


def match(institution: str | None) -> dict | None:
    """Return the most specific preset whose key is a substring of ``institution``."""
    if not institution:
        return None
    inst = institution.strip().lower()
    best_key: str | None = None
    for key in BANK_PRESETS:
        if key in inst and (best_key is None or len(key) > len(best_key)):
            best_key = key
    return BANK_PRESETS.get(best_key) if best_key else None
