"""The contract for analytics storage."""

from typing import Protocol
from uuid import UUID

from app.domains.analytics.interfaces.dtos import EventType


class EventRepository(Protocol):
    async def record_event(
        self, *, user_id: UUID, event_type: EventType
    ) -> None: ...
