"""Limits and defaults for events. No magic values elsewhere."""

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
