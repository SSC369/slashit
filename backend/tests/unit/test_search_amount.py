"""Epic 006, sub-plan 4.3 §7: C-33. A search that is a number (FR-30)."""

import pytest

from app.domains.capture.services.amount_reading import normalise_amount
from app.domains.expenses.constants import MAX_AMOUNT_PAISE
from app.domains.expenses.services.search_amount import amount_from_search

# One table for both readers, so expenses' copy cannot drift from capture's.
READ_AS_AMOUNT = [
    ("850", 85_000),
    ("₹850", 85_000),
    (" ₹ 850 ", 85_000),
    ("₹1,200", 120_000),
    ("₹1,20,000", 12_000_000),
    ("Rs 500", 50_000),
    ("rs.500", 50_000),
    ("INR 75", 7_500),
    ("1.2k", 120_000),
    ("3 lakh", 30_000_000),
    ("2.5 lakhs", 25_000_000),
    ("5 crore", 5_000_000_000),
    ("850.50", 85_050),
    ("850 rupees", 85_000),
    ("₹250/-", 25_000),
]

NOT_AN_AMOUNT = ["uber", "850 dinner", "850 900", "0", "-5", "", "₹", "850.505", "0.00"]


@pytest.mark.parametrize(("text", "paise"), READ_AS_AMOUNT)
def test_a_search_that_is_a_number_reads_as_capture_reads_it(
    text: str, paise: int
) -> None:
    assert amount_from_search(text=text) == paise
    assert normalise_amount(raw=text) == paise


@pytest.mark.parametrize("text", NOT_AN_AMOUNT)
def test_words_two_numbers_and_non_positive_amounts_are_not_an_amount(
    text: str,
) -> None:
    assert amount_from_search(text=text) is None


def test_an_amount_past_the_storage_ceiling_is_not_searched() -> None:
    """FR-2 as amended 2026-10-03: no row can hold it, so nothing is matched."""
    assert amount_from_search(text=str(MAX_AMOUNT_PAISE)) is None
    assert amount_from_search(text="92233720368547758.07") == MAX_AMOUNT_PAISE
