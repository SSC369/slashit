"""FR-20: the words a lookup searches for. Pure.

Lowercases, keeps runs of letters and digits, and drops the product's own
stop words. PostgreSQL's `english` configuration drops the ordinary ones
("what", "about", "my") and stems the rest, so "careers" finds "career".
Only letters and digits survive, which is what makes it safe to join the terms
into ``to_tsquery``'s syntax in the repository.
"""

import re

from app.domains.memories.constants import PRODUCT_STOP_WORDS

_WORD = re.compile(r"[a-z0-9]+")


def build_lookup_terms(*, text: str) -> list[str]:
    """The distinct search terms in ``text``, in the order typed."""
    terms: list[str] = []
    for word in _WORD.findall(text.lower()):
        if len(word) < 2 or word in PRODUCT_STOP_WORDS or word in terms:
            continue
        terms.append(word)
    return terms
