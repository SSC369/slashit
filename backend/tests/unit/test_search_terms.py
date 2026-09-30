"""Epic 005, sub-plan 4.1, C-3: search reads a line exactly as 004's
`/memories` lookup does (index §3)."""

import pytest

from app.domains.memories.constants import PRODUCT_STOP_WORDS as MEMORY_STOP_WORDS
from app.domains.memories.services.keyword_query import build_lookup_terms
from app.domains.search.constants import PRODUCT_STOP_WORDS as SEARCH_STOP_WORDS
from app.domains.search.services.terms import build_terms

SHARED_SAMPLE = [
    "passport",
    "Passport",
    "what do you remember about my career?",
    "When does my passport expire?",
    "renew passport renew",
    "backend engineer 2027",
    "Mom's birthday",
    "a b cd",
    "",
    "   ",
    "?!",
    "Spring-Boot REST_API",
    "know told recall memories memory",
    "Qatar Airways, Emirates",
    "₹850 dinner",
    "café résumé",
    "x" * 30,
    "tasks reminders memories",
    "What am I working toward?",
    "insurance renewal in 10 days",
]


@pytest.mark.parametrize("line", SHARED_SAMPLE)
def test_search_terms_match_the_memories_lookup(line: str) -> None:
    assert build_terms(text=line) == build_lookup_terms(text=line)


def test_the_stop_word_lists_are_the_same() -> None:
    assert SEARCH_STOP_WORDS == MEMORY_STOP_WORDS
