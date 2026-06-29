"""OFX / QFX parsing via the ofxparse library."""
from __future__ import annotations

import io
from decimal import Decimal

from app.domains.imports.parsers.base import RawTxn


def parse_ofx(content: bytes) -> list[RawTxn]:
    from ofxparse import OfxParser

    # ofxparse wants a byte stream; it handles both SGML (legacy) and XML OFX.
    ofx = OfxParser.parse(io.BytesIO(content))

    txns: list[RawTxn] = []
    for account in ofx.accounts:
        statement = account.statement
        for t in statement.transactions:
            desc = (t.payee or "") or (getattr(t, "memo", "") or "")
            txns.append(
                RawTxn(
                    date=t.date.date() if hasattr(t.date, "date") else t.date,
                    amount=Decimal(str(t.amount)),   # already signed in OFX
                    description=desc.strip(),
                )
            )
    return txns
