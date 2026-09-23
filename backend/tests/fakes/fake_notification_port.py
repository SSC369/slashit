"""In-memory stand-ins for reminders' NotificationPort and FiringQueuePort."""

from datetime import datetime
from uuid import UUID

from app.domains.reminders.interfaces.dtos import FiringAnnouncement, UserActionValue


class FakeNotificationPort:
    """Keeps one announcement per firing, as the real list does (AD-3)."""

    def __init__(self, *, fail_next_announce: bool = False) -> None:
        self.announcements: dict[UUID, FiringAnnouncement] = {}
        self.announce_calls = 0
        self.actions: list[tuple[UUID, UserActionValue]] = []
        self.fail_next_announce = fail_next_announce

    async def announce_firing(self, *, announcement: FiringAnnouncement) -> None:
        self.announce_calls += 1
        if self.fail_next_announce:
            self.fail_next_announce = False
            raise ConnectionError("notification write failed")
        self.announcements.setdefault(announcement.firing_id, announcement)

    async def record_action(
        self,
        *,
        user_id: UUID,
        firing_id: UUID,
        action: UserActionValue,
        acted_at: datetime,
    ) -> None:
        self.actions.append((firing_id, action))


class FakeFiringQueue:
    """Refuses to queue an occurrence twice while it is still queued."""

    def __init__(self) -> None:
        self.queued: set[tuple[UUID, datetime]] = set()

    async def enqueue_firing(
        self, *, reminder_id: UUID, scheduled_for: datetime
    ) -> bool:
        key = (reminder_id, scheduled_for)
        if key in self.queued:
            return False
        self.queued.add(key)
        return True
