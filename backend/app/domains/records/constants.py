"""Limits and job settings for records. No magic values elsewhere."""

from typing import Final

# Must equal the column in migration 0032 and the gateway's EMBEDDING_DIMENSIONS.
TASK_EMBEDDING_DIMENSIONS: Final = 768

# Epic 005 build plan §6: the embed job's attempts before leaving the vector
# NULL for the periodic backfill.
EMBED_MAX_ATTEMPTS: Final = 3

# Epic 005 AD-7, following 004 P-6: the periodic sweep only looks at recent
# rows; the full sweep at deploy (FR-13) looks at every row.
EMBEDDING_BACKFILL_BATCH: Final = 100
EMBEDDING_BACKFILL_WINDOW_HOURS: Final = 24

# Epic 005 index §6: the full sweep spaces its embed jobs so the provider sees
# about this many calls a second, `estimate`.
BACKFILL_CALLS_PER_SECOND: Final = 5
