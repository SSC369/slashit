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

# FR-39: reminder emails per user per local day. Past it, the list still fills.
MAX_EMAILS_PER_DAY: Final[int] = 50

# FR-14 with AD-3: a send is retried, then marked failed; the list row stands.
SEND_EMAIL_MAX_ATTEMPTS: Final[int] = 5

# The panel's cap notice (design §8, `NotificationPanel`).
EMAIL_PAUSED_TITLE: Final[str] = "Email paused until tomorrow"
EMAIL_PAUSED_DETAIL: Final[str] = (
    "You reached 50 reminder emails today. Reminders keep landing here."
)

RESEND_EMAILS_URL: Final[str] = "https://api.resend.com/emails"
RESEND_TIMEOUT_SECONDS: Final[float] = 10.0
