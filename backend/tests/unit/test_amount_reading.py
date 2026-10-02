"""Epic 006, sub-plan 4.1 §7: C-1 to C-3. Reading rupee amounts by code."""

import pytest

from app.domains.capture.services.amount_reading import (
    keep_candidates,
    names_foreign_currency,
    normalise_amount,
    numbers_in,
)


@pytest.mark.parametrize(
    ("raw", "paise"),
    [
        ("₹850", 85_000),
        ("850", 85_000),
        ("₹1,200", 120_000),
        ("₹1,20,000", 12_000_000),
        ("120,000", 12_000_000),
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
    ],
)
def test_normalise_amount_reads_every_form_fr_2_names(raw: str, paise: int) -> None:
    """C-1."""
    assert normalise_amount(raw=raw) == paise


@pytest.mark.parametrize("raw", ["0", "-5", "abc", "", "₹", "850.505", "0.00"])
def test_normalise_amount_rejects_what_is_not_a_positive_amount(raw: str) -> None:
    """C-1."""
    assert normalise_amount(raw=raw) is None


def test_numbers_in_finds_every_amount_shaped_number() -> None:
    assert numbers_in(text="2 coffees 180 at 1.2k cafe, ₹1,20,000") == {
        200,
        18_000,
        120_000,
        12_000_000,
    }


def test_numbers_in_ignores_digits_glued_to_letters() -> None:
    assert numbers_in(text="b2b lunch") == set()


def test_keep_candidates_drops_a_number_the_user_never_typed() -> None:
    """C-2, AD-4: a made-up amount never reaches a total."""
    assert keep_candidates(model_amounts=["900", "850"], text="dinner 850") == [85_000]


def test_keep_candidates_keeps_order_and_drops_repeats() -> None:
    """C-2."""
    assert keep_candidates(
        model_amounts=["180", "2", "₹180"], text="2 coffees 180"
    ) == [18_000, 200]


def test_keep_candidates_matches_across_forms() -> None:
    """The model may write 1200 for a typed 1.2k; both are 120,000 paise."""
    assert keep_candidates(model_amounts=["1200"], text="shoes 1.2k") == [120_000]


@pytest.mark.parametrize(
    "text", ["$20 lunch", "20 USD", "€5 coffee", "AED 40 taxi", "30 dollars", "£12"]
)
def test_names_foreign_currency_is_true_for_another_currency(text: str) -> None:
    """C-3."""
    assert names_foreign_currency(text=text) is True


@pytest.mark.parametrize("text", ["₹20 tea", "Rs 20", "20", "500 kg rice", "used tea"])
def test_names_foreign_currency_is_false_for_rupees(text: str) -> None:
    """C-3."""
    assert names_foreign_currency(text=text) is False
