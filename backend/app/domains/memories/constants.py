"""Limits, words and the model contract for memories. No magic values elsewhere."""

from typing import Any, Final

# FR-4. Checked on the fact, never on the whole command line (AD-7).
MAX_FACT_LENGTH: Final = 500

# Build plan AD-5: the model only ever sees this many of the user's memories.
CANDIDATE_LIMIT: Final = 10

# Must equal the column in migration 0024 and the gateway's EMBEDDING_DIMENSIONS.
MEMORY_EMBEDDING_DIMENSIONS: Final = 768

# FR-20. Words that name the act of remembering rather than what is
# remembered. PostgreSQL's `english` configuration drops the rest ("what",
# "about", "my"), so only these are dropped in code.
PRODUCT_STOP_WORDS: Final = frozenset(
    {"remember", "remembered", "memory", "memories", "know", "told", "recall"}
)

# FR-20. How many matches one lookup returns. Enough for a chat card.
LOOKUP_LIMIT: Final = 20

# Build plan §6: the reembed job's attempts before leaving the vector NULL.
REEMBED_MAX_ATTEMPTS: Final = 3

# Descriptions kept terse on purpose: 001's dev log I-1 measured a verbose
# schema description doubling generation latency.
JUDGEMENT_SCHEMA: Final[dict[str, Any]] = {
    "type": "object",
    "properties": {
        "category": {
            "type": "string",
            "enum": ["personal", "people", "professional", "life", "none"],
        },
        "conflicting_ids": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["category", "conflicting_ids"],
}

JUDGEMENT_INSTRUCTION: Final = (
    "Classify the fact: personal (preferences, interests, plans), people "
    "(family, friends, colleagues), professional (career, skills, work), life "
    "(documents, subscriptions, purchases, travel, decisions), or none. "
    "In conflicting_ids list the ids of candidates the fact directly "
    "contradicts; [] if none."
)
