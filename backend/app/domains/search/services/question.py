"""FR-15: whether a search's text reads as a question. Pure.

Only a question gets a written answer, so a word search stays instant and
never calls the model (build plan Q1, PRD question 1).
"""

import re

from app.domains.search.constants import QUESTION_WORDS

_FIRST_WORD = re.compile(r"[a-z]+")


def is_question(*, text: str) -> bool:
    """True when ``text`` ends in "?" or starts with a question word."""
    stripped = text.strip()
    if stripped.endswith("?"):
        return True
    first_word = _FIRST_WORD.match(stripped.lower())
    return first_word is not None and first_word.group() in QUESTION_WORDS
