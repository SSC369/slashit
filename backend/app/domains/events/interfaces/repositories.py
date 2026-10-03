"""The contract for event storage."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domains.events.interfaces.dtos import (
    EventLimitReached,
    EventWrite,
    StoredEventDTO,
)


class EventRepository(Protocol):
    async def create_event_if_upcoming_below(
        self, *, user_id: UUID, write: EventWrite, limit: int, now: datetime
    ) -> StoredEventDTO | None:
        """Insert when the user holds fewer than ``limit`` upcoming events,
        counted and inserted under one per-user lock so two creates cannot
        both pass at ``limit - 1`` (FR-31). None when the count was reached."""
        ...

    async def update_event_if_upcoming_below(
        self,
        *,
        user_id: UUID,
        event_id: UUID,
        write: EventWrite,
        limit: int,
        now: datetime,
    ) -> StoredEventDTO | EventLimitReached | None:
        """Replace a live event's columns, under the same per-user lock as a
        create. ``EventLimitReached`` when the edit would make it upcoming
        while ``limit`` others are (FR-31); None when no live event with this
        id is the user's."""
        ...

    async def soft_delete(self, *, user_id: UUID, event_id: UUID) -> bool:
        """False when no live event with this id is the user's."""
        ...

    async def list_for_user(self, *, user_id: UUID) -> list[StoredEventDTO]:
        """Every live event the user owns, unordered."""
        ...

    async def get_by_id(
        self, *, user_id: UUID, event_id: UUID
    ) -> StoredEventDTO | None: ...

    async def set_alert_leads(
        self, *, user_id: UUID, event_id: UUID, leads: tuple[int, ...]
    ) -> None:
        """Store only the leads whose alerts were set (FR-19, FR-33)."""
        ...
