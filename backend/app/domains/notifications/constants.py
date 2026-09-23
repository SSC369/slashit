"""Notifications' limits and names. No magic values elsewhere."""

from typing import Final

# FR-35: the panel loads this many at a time.
NOTIFICATION_PAGE_SIZE: Final[int] = 30

# AD-4: the one LISTEN/NOTIFY channel. Payload carries ids only, never text.
NOTIFY_CHANNEL: Final[str] = "slashit_notifications"

# Reconnect backoff for the LISTEN connection, in seconds.
LISTEN_RETRY_FIRST_SECONDS: Final[float] = 1.0
LISTEN_RETRY_MAX_SECONDS: Final[float] = 30.0
LISTEN_HEALTH_CHECK_SECONDS: Final[float] = 5.0
