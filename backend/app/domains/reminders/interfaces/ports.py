"""What reminders needs from other domains, in its own words.

Per repo-rules.md section 6, the port belongs to the consumer. It names the
one thing reminders needs and not the domain that supplies it.
"""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domains.reminders.interfaces.dtos import (
    FiringAnnouncement,
    UserActionValue,
    UserClockDTO,
)


class UserClockPort(Protocol):
    """Where the user is, and the time a date-only reminder takes (FR-3)."""

    async def get_user_clock(self, *, user_id: UUID) -> UserClockDTO: ...


class NotificationPort(Protocol):
    """Telling the user that a reminder fired, and what they did about it."""

    async def announce_firing(self, *, announcement: FiringAnnouncement) -> None:
        """Safe to repeat: one list entry per firing, however often called."""
        ...

    async def record_action(
        self,
        *,
        user_id: UUID,
        firing_id: UUID,
        action: UserActionValue,
        acted_at: datetime,
    ) -> None: ...


class FiringQueuePort(Protocol):
    """Queueing one firing job per due occurrence (AD-2)."""

    async def enqueue_firing(
        self, *, reminder_id: UUID, scheduled_for: datetime
    ) -> bool:
        """False when that occurrence's job is already queued."""
        ...
