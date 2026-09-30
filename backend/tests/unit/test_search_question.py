"""Epic 005, sub-plan 4.2, C-2.1: FR-15's question rule."""

import pytest

from app.domains.search.services.question import is_question


@pytest.mark.parametrize(
    "text",
    [
        "when does my passport expire?",
        "passport?",
        "What am I working toward",
        "WHO is my doctor",
        "how much is my SIP",
        "which airline do I prefer",
        "do I have a dentist appointment",
        "does Priya live in Pune",
        "did I renew the insurance",
        "is my loan repaid",
        "are there tasks for the wedding",
        "am I allergic to anything",
        "have I paid rent",
        "has the FD matured",
        "where does Arjun work",
        "why did I stop guitar",
        "  when is Mom's birthday  ",
    ],
)
def test_a_question_is_recognised(text: str) -> None:
    assert is_question(text=text) is True


@pytest.mark.parametrize(
    "text",
    ["passport", "whatever happened", "career goals", "renew passport", "", "?!x"],
)
def test_a_word_search_is_not_a_question(text: str) -> None:
    assert is_question(text=text) is False
