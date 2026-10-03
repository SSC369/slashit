"""PRD FR-30: a search that is a number. Pure, no model.

Reads the whole search as one rupee amount, with the rules an expense line is
read by: "850", "₹850", "1,200", "850.50", "1.2k", "3 lakh". A copy of
capture's whole-amount rules (``capture/services/amount_reading.py``), as
search's ``terms.py`` copies 004's term builder: search reaches expenses only
through its port, and capture's reader is capture's own. C-33 runs both over
one table so they cannot drift.
"""

import re
from decimal import Decimal, InvalidOperation

from app.domains.expenses.constants import MAX_AMOUNT_PAISE

_PAISE_PER_RUPEE = 100

# Longer spellings first, so "lakhs" is not read as "lakh" plus a stray "s".
_MULTIPLIERS: dict[str, int] = {
    "crores": 10_000_000,
    "crore": 10_000_000,
    "cr": 10_000_000,
    "lakhs": 100_000,
    "lakh": 100_000,
    "lacs": 100_000,
    "lac": 100_000,
    "k": 1_000,
}

_WHOLE_AMOUNT = re.compile(
    r"^(?:(?:₹|rs\.?|inr|rupees?)\s*)?"
    r"(?P<number>\d+(?:,\d+)*(?:\.\d+)?)"
    rf"\s*(?P<unit>{'|'.join(_MULTIPLIERS)})?"
    r"\s*(?:rupees?|rs\.?|/-)?$",
    re.IGNORECASE,
)


def amount_from_search(*, text: str) -> int | None:
    """The search as paise, or None when it is not exactly one positive
    amount, or is past the storage ceiling (FR-2)."""
    match = _WHOLE_AMOUNT.match(text.strip())
    if match is None:
        return None
    try:
        rupees = Decimal(match.group("number").replace(",", ""))
    except InvalidOperation:
        return None
    unit = match.group("unit")
    if unit is not None:
        rupees *= _MULTIPLIERS[unit.lower()]
    paise = rupees * _PAISE_PER_RUPEE
    if paise <= 0 or paise != paise.to_integral_value() or paise > MAX_AMOUNT_PAISE:
        return None
    return int(paise)
