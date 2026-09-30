"""Limits, thresholds and words for search. No magic values elsewhere."""

from typing import Final

# FR-3: a search's text, after the command, is at most this long.
MAX_SEARCH_LENGTH: Final = 500

# FR-7: at most this many records shown per record type in the capture card.
GROUP_LIMIT: Final = 5

# How many candidates one record domain returns to a search, before ranking.
# Enough to fill every group and rank within it; totals are counted separately.
PORT_LIMIT: Final = 50

# AD-3: a record matched by meaning alone must be closer than this, by cosine
# distance. `estimate` until the search evaluation set tunes it (T-1.13).
MEANING_MAX_DISTANCE: Final = 0.35

# AD-4, build plan Q5: how long a search waits for the query's vector before
# returning word matches only (FR-20).
SEARCH_EMBED_TIMEOUT_SECONDS: Final = 2.5

# FR-4. Words that name the act of remembering rather than what is sought.
# A copy of 004's rule (memories/constants.py), pinned to it by
# tests/unit/test_search_terms.py, so `/search` and `/memories` read a line
# the same way (index §3).
PRODUCT_STOP_WORDS: Final = frozenset(
    {"remember", "remembered", "memory", "memories", "know", "told", "recall"}
)
