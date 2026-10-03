"""Limits and defaults for events. No magic values elsewhere."""

from datetime import timedelta
from typing import Final

# FR-31: at most this many upcoming events. Past one-time events do not count;
# a yearly event always does. `estimate`, carried from the epic.
MAX_UPCOMING_EVENTS: Final = 500

# The migration's check constraints agree with these (index §5).
MAX_TITLE_LENGTH: Final = 200
MAX_LOCATION_LENGTH: Final = 200
MAX_DESCRIPTION_LENGTH: Final = 2000
# One year. A longer lead is read as no alert.
MAX_ALERT_LEAD_MINUTES: Final = 525600

MINUTES_PER_HOUR: Final = 60
MINUTES_PER_DAY: Final = 1440
MINUTES_PER_WEEK: Final = 10080

# Must equal the column in migration 0037 and the gateway's EMBEDDING_DIMENSIONS.
EVENT_EMBEDDING_DIMENSIONS: Final = 768

# Build plan AD-4: the roll job's batch, every 15 minutes.
ROLL_BATCH: Final = 200
# The sweep leaves an event this long after its write before arming it, so a
# request still arming it is not raced (dev log D-20).
ALERTS_PENDING_GRACE: Final = timedelta(minutes=2)
# NFR-4: pending longer than this is out of step, and counted nightly.
ALERTS_OUT_OF_STEP_AFTER: Final = timedelta(hours=1)
REZONE_MAX_ATTEMPTS: Final = 5

# Epic 005 AD-7, as reminders and expenses: the embed job and its backfill.
EMBED_MAX_ATTEMPTS: Final = 3
EMBEDDING_BACKFILL_BATCH: Final = 100
EMBEDDING_BACKFILL_WINDOW_HOURS: Final = 24
BACKFILL_CALLS_PER_SECOND: Final = 5
