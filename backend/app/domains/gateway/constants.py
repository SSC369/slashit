"""Limits, budgets and policy for the gateway. No magic values elsewhere."""

from typing import Final

# Requirement NFR-4. `estimate`: chosen because a capture is a foreground action
# and a user will not wait longer. Measure against real p95 once epic 001 calls
# this, and revise here.
PROVIDER_TIMEOUT_SECONDS: Final = 8.0

# Requirement FR-20. One retry, and only where retrying is safe: a connection
# that never established. A timeout is never retried, because the first attempt
# may still be running and a retry would double the spend.
MAX_ATTEMPTS: Final = 2
RETRY_BACKOFF_SECONDS: Final = 0.5

# Requirement FR-10. The fallback when a user has no ai_user_limit row. The row
# is authoritative; this exists so a user without one is limited rather than
# unlimited.
DEFAULT_REQUESTS_PER_DAY: Final = 20

# The window the limit is counted over.
LIMIT_WINDOW_HOURS: Final = 24

PROVIDER_NAME: Final = "google"

# Epic 004 AD-4. Every vector stored in memories.embedding has this length, so
# changing it means re-embedding every memory, not editing this line.
EMBEDDING_DIMENSIONS: Final = 768

# Epic 004. An embedding is short (one fact, at most 500 characters) and sits
# inside the save's 8 second budget beside the generation. `estimate`.
EMBED_TIMEOUT_SECONDS: Final = 3.0
