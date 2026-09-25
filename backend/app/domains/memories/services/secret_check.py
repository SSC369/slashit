"""FR-8, AD-8: does a fact look like a secret. Pure, no model, no I/O.

Deterministic on purpose: it must hold while the model is down, it must be
testable case by case, and it costs nothing. It names the kind of secret, and
never returns or logs the matched text.
"""

import re

from app.domains.memories.interfaces.dtos import SecretKind

# 13 to 19 digits, allowing the spaces and dashes people type in card numbers.
_CARD_CANDIDATE = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
# A 12-digit national ID number, typed whole or in groups of four, standing
# alone: not the first twelve digits of a longer grouped number.
_ID_NUMBER = re.compile(r"(?<!\d)(?<!\d[ -])\d{4}[ -]?\d{4}[ -]?\d{4}(?!\d)(?![ -]\d)")
# The tax-ID shape AAAAA9999A.
_TAX_ID = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b", re.IGNORECASE)
# A credential word next to something with a digit in it: "PIN 4417",
# "password is hunter2", "cvv: 123".
_CREDENTIAL = re.compile(
    r"\b(?:password|passcode|pin|cvv|otp)\b\W{0,3}(?:is\W+)?\S*\d",
    re.IGNORECASE,
)


def detect_secret(*, text: str) -> SecretKind | None:
    """The first kind of secret the text looks like, or None."""
    for match in _CARD_CANDIDATE.finditer(text):
        digits = re.sub(r"\D", "", match.group())
        if 13 <= len(digits) <= 19 and _passes_luhn(digits=digits):
            return SecretKind.CARD
    if _ID_NUMBER.search(text):
        return SecretKind.ID_NUMBER
    if _TAX_ID.search(text):
        return SecretKind.TAX_ID
    if _CREDENTIAL.search(text):
        return SecretKind.CREDENTIAL
    return None


def _passes_luhn(*, digits: str) -> bool:
    """The checksum every payment card number carries."""
    total = 0
    for position, character in enumerate(reversed(digits)):
        digit = int(character)
        if position % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0
