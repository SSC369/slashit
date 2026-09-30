"""Limits and the extraction contract for reminders. No magic values elsewhere."""

from datetime import timedelta
from typing import Final

# FR-38, build plan Q9's companion: at most this many live, not-done reminders.
MAX_ACTIVE_REMINDERS: Final = 100

# FR-6. A repeat interval is 1 to 99; the migration's check constraint agrees.
MIN_REPEAT_INTERVAL: Final = 1
MAX_REPEAT_INTERVAL: Final = 99

# AD-11: lateness is measured from the occurrence's set time to its firing.
ON_TIME_WINDOW: Final = timedelta(minutes=5)
MISSED_AFTER: Final = timedelta(hours=24)

# FR-21: the two fixed snoozes. The third, tomorrow, uses the default time.
SNOOZE_SHORT: Final = timedelta(minutes=10)
SNOOZE_LONG: Final = timedelta(hours=1)

# How many due reminders one sweep reads. The rest wait a minute; each is
# still fired, and its lateness says so (AD-11).
FIRE_DUE_BATCH: Final = 5000

# FR-16: a failed firing job retries, and the unique firing row makes it safe.
FIRE_ONE_MAX_ATTEMPTS: Final = 5

# NFR-4: a live reminder this far past due with no firing is lost. The same
# 5 minutes after which a firing counts as late.
LOST_AFTER: Final = ON_TIME_WINDOW
# At most this many lost reminders are read and logged per reconciliation.
RECONCILE_BATCH: Final = 1000

# A firing can land between a rezone's read and its write; the rezone then
# re-reads and tries again this many times in all.
REZONE_MAX_PASSES: Final = 3
# A failed timezone_changed job retries; each run skips what already moved.
REZONE_MAX_ATTEMPTS: Final = 5

# Must equal the column in migration 0033 and the gateway's EMBEDDING_DIMENSIONS.
REMINDER_EMBEDDING_DIMENSIONS: Final = 768

# Epic 005 build plan §6 and AD-7, as for tasks in records/constants.py.
EMBED_MAX_ATTEMPTS: Final = 3
EMBEDDING_BACKFILL_BATCH: Final = 100
EMBEDDING_BACKFILL_WINDOW_HOURS: Final = 24

# Epic 005 index §6: the full sweep spaces its embed jobs so the provider sees
# about this many calls a second, `estimate`.
BACKFILL_CALLS_PER_SECOND: Final = 5
