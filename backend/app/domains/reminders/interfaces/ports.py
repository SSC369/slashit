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

    async def hide_for_reminder(self, *, user_id: UUID, reminder_id: UUID) -> None:
        """The reminder is gone: every notification about it stops showing."""
        ...


class FiringQueuePort(Protocol):
    """Queueing one firing job per due occurrence (AD-2)."""

    async def enqueue_firing(
        self, *, reminder_id: UUID, scheduled_for: datetime
    ) -> bool:
        """False when that occurrence's job is already queued."""
        ...


class ReminderEmbeddingPort(Protocol):
    """What reminders needs to give a reminder a meaning vector (epic 005
    AD-7). None when the model refused; the job then retries."""

    async def embed_reminder_description(
        self, *, user_id: UUID, description: str
    ) -> tuple[float, ...] | None: ...


class ReminderEmbedQueue(Protocol):
    """Queues a reminder's vector after a create or an edit, so neither waits
    on, or fails with, the model (005 build plan §7)."""

    async def queue_reminder_embed(
        self, *, user_id: UUID, reminder_id: UUID, delay_seconds: int
    ) -> None: ...
