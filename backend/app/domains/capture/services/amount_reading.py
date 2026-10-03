"""Reads rupee amounts out of typed text. Pure functions, no model.

Build plan AD-4: the model lists candidate amounts and code keeps only those
whose number appears in what the user typed, so a made-up number never reaches
a total (NFR-5). AD-8: another currency is refused before any model call.

Every amount is integer paise (AD-2). ``Decimal`` is used only while reading,
so ``1.2k`` and ``1,200.50`` convert exactly.
"""

import re
from decimal import Decimal, InvalidOperation

_PAISE_PER_RUPEE = 100

# FR-2's Indian units and ``k``. Longer spellings first, so "lakhs" is not read
# as "lakh" plus a stray "s".
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
_MULTIPLIER_PATTERN = "|".join(_MULTIPLIERS)

_RUPEE_PREFIX = r"(?:₹|rs\.?|inr|rupees?)"

# One amount: an optional rupee marker, digits with commas in any grouping,
# up to two decimals, and an optional unit. Digits glued to letters on the
# left, such as the 2 in "b2b", are not amounts.
_AMOUNT_PATTERN = re.compile(
    rf"(?<![\w.])(?:{_RUPEE_PREFIX}\s*)?"
    r"(?P<number>\d+(?:,\d+)*(?:\.\d+)?)"
    rf"(?:\s*(?P<unit>{_MULTIPLIER_PATTERN})\b)?",
    re.IGNORECASE,
)

_WHOLE_AMOUNT = re.compile(
    rf"^(?:{_RUPEE_PREFIX}\s*)?"
    r"(?P<number>\d+(?:,\d+)*(?:\.\d+)?)"
    rf"\s*(?P<unit>{_MULTIPLIER_PATTERN})?"
    r"\s*(?:rupees?|rs\.?|/-)?$",
    re.IGNORECASE,
)

_FOREIGN_CURRENCY = re.compile(
    r"[$€£¥]"
    r"|\b(?:usd|eur|gbp|aed|sgd|aud|cad|jpy|chf|cny|hkd|nzd|myr|thb|sar|qar)\b"
    r"|\b(?:dollars?|euros?|dirhams?|yen|yuan|ringgit|baht|riyals?)\b",
    re.IGNORECASE,
)


def normalise_amount(*, raw: str) -> int | None:
    """One typed amount as paise, or None if it is not a positive amount.

    "₹1,20,000" is 12,000,000 paise; "1.2k" is 120,000; "3 lakh" and
    "5 crore" are read; "850.50" keeps its paise. More than two decimals,
    after the unit is applied, is not an amount.
    """
    match = _WHOLE_AMOUNT.match(raw.strip())
    if match is None:
        return None
    return _to_paise(number=match.group("number"), unit=match.group("unit"))


def numbers_in(*, text: str) -> set[int]:
    """Every amount-shaped number in the text, in paise."""
    amounts: set[int] = set()
    for match in _AMOUNT_PATTERN.finditer(text):
        paise = _to_paise(number=match.group("number"), unit=match.group("unit"))
        if paise is not None:
            amounts.add(paise)
    return amounts


def keep_candidates(*, model_amounts: list[str], text: str) -> list[int]:
    """The model's amounts that appear in the text, distinct, in its order."""
    typed_amounts = numbers_in(text=text)
    kept: list[int] = []
    for model_amount in model_amounts:
        paise = normalise_amount(raw=model_amount)
        if paise is not None and paise in typed_amounts and paise not in kept:
            kept.append(paise)
    return kept


def names_foreign_currency(*, text: str) -> bool:
    """True when the text names a currency other than the rupee (FR-6)."""
    return _FOREIGN_CURRENCY.search(text) is not None


def _to_paise(*, number: str, unit: str | None) -> int | None:
    try:
        rupees = Decimal(number.replace(",", ""))
    except InvalidOperation:
        return None
    if unit is not None:
        rupees *= _MULTIPLIERS[unit.lower()]
    paise = rupees * _PAISE_PER_RUPEE
    if paise <= 0 or paise != paise.to_integral_value():
        return None
    return int(paise)
