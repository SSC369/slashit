"""Limits, thresholds and words for search. No magic values elsewhere."""

from typing import Any, Final

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

# AD-6: a related record must be closer than this to the record it is listed
# on, by cosine distance. Tighter than AD-3's bar: a related list has no words
# to lean on. `estimate` until the related set tunes it (sub-plan 4.3, T-3.9).
RELATED_MAX_DISTANCE: Final = 0.30

# FR-25: at most this many related records on a detail.
RELATED_LIMIT: Final = 5

# Build plan §4: the records view's `search` returns at most this many a page.
PAGE_LIMIT_MAX: Final = 50

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

# FR-15: input is a question when it ends in "?" or starts with one of these.
QUESTION_WORDS: Final = frozenset(
    {
        "what",
        "when",
        "where",
        "who",
        "why",
        "how",
        "which",
        "do",
        "does",
        "did",
        "is",
        "are",
        "am",
        "have",
        "has",
    }
)

# Build plan Q4 and AD-5: the answer reads only the top ranked records, and
# keeps at most this many sentences (FR-16).
ANSWER_RECORD_LIMIT: Final = 10
ANSWER_SENTENCE_LIMIT: Final = 4

# Build plan §5. Descriptions kept terse: 001's dev log I-1 measured a verbose
# schema description doubling generation latency.
ANSWER_SCHEMA: Final[dict[str, Any]] = {
    "type": "object",
    "properties": {
        "sentences": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "sources": {"type": "array", "items": {"type": "integer"}},
                },
                "required": ["text", "sources"],
            },
        },
        "supported": {"type": "boolean"},
    },
    "required": ["sentences", "supported"],
}

ANSWER_INSTRUCTION: Final = (
    "Answer the question using only the numbered records. "
    "Write at most four short sentences. "
    "Every sentence lists in sources the numbers of the records it rests on. "
    "Never write a record's number in the text. "
    "If the records do not answer the question, return no sentences and "
    "supported false. Do not guess."
)
