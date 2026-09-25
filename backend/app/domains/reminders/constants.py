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
