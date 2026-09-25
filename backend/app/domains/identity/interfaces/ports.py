"""What identity needs from outside itself, in identity's own words."""

from typing import Protocol
from uuid import UUID


class TimezoneChangeQueuePort(Protocol):
    async def enqueue_timezone_change(self, *, user_id: UUID) -> None:
        """Announce that the user's timezone changed, after it is saved. Who
        listens is not identity's business (build plan AD-6)."""
        ...
