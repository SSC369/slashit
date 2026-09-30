"""FR-4: the words a search matches on. Pure.

A copy of 004's ``build_lookup_terms`` (index §3): lowercases, keeps runs of
letters and digits, and drops the product's own stop words. PostgreSQL's
`english` configuration drops the ordinary ones ("what", "my") and stems the
rest, so "passports" finds "passport". Only letters and digits survive, which
is what makes it safe to join the terms into ``to_tsquery``'s syntax.
"""

import re

from app.domains.search.constants import PRODUCT_STOP_WORDS

_WORD = re.compile(r"[a-z0-9]+")


def build_terms(*, text: str) -> list[str]:
    """The distinct search terms in ``text``, in the order typed."""
    terms: list[str] = []
    for word in _WORD.findall(text.lower()):
        if len(word) < 2 or word in PRODUCT_STOP_WORDS or word in terms:
            continue
        terms.append(word)
    return terms
