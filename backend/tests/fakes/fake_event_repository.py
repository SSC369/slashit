"""An in-memory EventRepository. Not a mock: it behaves, so tests read as
behaviour."""

import uuid

from app.domains.analytics.interfaces.dtos import EventType


class FakeEventRepository:
    """Satisfies analytics' EventRepository Protocol without inheriting from it."""

    def __init__(self) -> None:
        self.rows: list[tuple[uuid.UUID, EventType]] = []

    async def record_event(self, *, user_id: uuid.UUID, event_type: EventType) -> None:
        self.rows.append((user_id, event_type))
