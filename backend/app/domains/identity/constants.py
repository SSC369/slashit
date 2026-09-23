"""Limits and defaults for identity. No magic values elsewhere."""

from datetime import time, timedelta
from typing import Final

# Used only if the browser could not detect a timezone at all (Intl throws or
# returns undefined) and the client omits detectedTimezone entirely.
DEFAULT_TIMEZONE: Final = "UTC"

# Epic 003 FR-31, FR-32: the reminder settings a user has until they change
# them. Migration 0017 sets the same defaults on the columns.
DEFAULT_REMINDER_TIME: Final = time(9, 0)
DEFAULT_POPUPS_ENABLED: Final = True
DEFAULT_EMAIL_ENABLED: Final = True

# FR-8: how long an account may sit unverified before purge_unverified_accounts
# (jobs.py) removes it, freeing its email for a later signup.
UNVERIFIED_ACCOUNT_TTL: Final = timedelta(hours=24)

# FR-17: sign-in lockout, moved into the app 2026-09-19 (the Password
# Verification Attempt hook is Teams/Enterprise only). Same numbers the
# dropped SQL hook used.
SIGN_IN_MAX_FAILED_ATTEMPTS: Final = 5
SIGN_IN_ATTEMPT_WINDOW: Final = timedelta(minutes=15)
SIGN_IN_LOCKOUT_DURATION: Final = timedelta(minutes=15)
