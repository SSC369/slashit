"""C-8 of sub-plan 4.1, the pure half: which words a lookup searches for."""

from app.domains.memories.services.keyword_query import build_lookup_terms


def test_product_words_are_dropped_and_the_rest_kept_in_order() -> None:
    terms = build_lookup_terms(text="What do you remember about my career?")

    # "what", "do", "you", "about", "my" are dropped by PostgreSQL's english
    # configuration in the repository, not here.
    assert "remember" not in terms
    assert terms[-1] == "career"


def test_punctuation_never_reaches_the_query() -> None:
    terms = build_lookup_terms(text="passport | expiry & (2030)!")

    assert terms == ["passport", "expiry", "2030"]


def test_repeats_and_single_letters_are_dropped() -> None:
    assert build_lookup_terms(text="a visa visa VISA") == ["visa"]


def test_only_product_words_gives_no_terms() -> None:
    assert build_lookup_terms(text="memories I told you to remember") == [
        "you",
        "to",
    ]
