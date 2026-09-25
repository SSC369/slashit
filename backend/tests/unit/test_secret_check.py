"""C-7 of sub-plan 4.1: FR-8's caution, and AD-8's patterns, case by case."""

import pytest

from app.domains.memories.interfaces.dtos import SecretKind
from app.domains.memories.services.secret_check import detect_secret


@pytest.mark.parametrize(
    ("fact", "expected"),
    [
        ("bank card 4111 1111 1111 1111", SecretKind.CARD),
        ("card 4111-1111-1111-1111 expires 09/28", SecretKind.CARD),
        ("Aadhaar is 1234 5678 9012", SecretKind.ID_NUMBER),
        ("PAN is ABCDE1234F", SecretKind.TAX_ID),
        ("Locker PIN 4417", SecretKind.CREDENTIAL),
        ("wifi password is hunter2", SecretKind.CREDENTIAL),
        ("the cvv: 123", SecretKind.CREDENTIAL),
    ],
)
def test_secret_shapes_are_flagged(fact: str, expected: SecretKind) -> None:
    assert detect_secret(text=fact) == expected


@pytest.mark.parametrize(
    "fact",
    [
        "born in 1990",
        "My passport expires in 2030",
        "call Rahul on 98450 12345",
        "card 4111 1111 1111 1112",  # 16 digits, fails the Luhn check
        "pinned the map to the wall",
        "the password is on a sticky note",
        "OTP comes by SMS",
    ],
)
def test_ordinary_facts_are_not_flagged(fact: str) -> None:
    assert detect_secret(text=fact) is None
