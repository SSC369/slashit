"""An in-memory TimezoneChangeQueuePort: records who was announced."""

from uuid import UUID


class FakeTimezoneChangeQueue:
    def __init__(self) -> None:
        self.announced_user_ids: list[UUID] = []

    async def enqueue_timezone_change(self, *, user_id: UUID) -> None:
        self.announced_user_ids.append(user_id)
