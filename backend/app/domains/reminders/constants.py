"""Limits and the extraction contract for reminders. No magic values elsewhere."""

from typing import Final

# FR-38, build plan Q9's companion: at most this many live, not-done reminders.
MAX_ACTIVE_REMINDERS: Final = 100

# FR-6. A repeat interval is 1 to 99; the migration's check constraint agrees.
MIN_REPEAT_INTERVAL: Final = 1
MAX_REPEAT_INTERVAL: Final = 99
