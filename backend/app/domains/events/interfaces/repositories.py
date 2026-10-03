"""The contract for event storage."""

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domains.events.interfaces.dtos import (
    EventLimitReached,
    EventTargetDTO,
    EventText,
    EventWrite,
    StoredEventDTO,
    StoredEventSearchPageDTO,
)
from app.domains.events.services.schedule import LocalSchedule


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

    async def finish_arming(
        self, *, user_id: UUID, event_id: UUID, leads: tuple[int, ...]
    ) -> None:
        """Store only the leads whose alerts were set (FR-19, FR-33), and
        mark the alerts as no longer pending (dev log D-20)."""
        ...

    async def mark_alerts_pending(self, *, user_id: UUID, event_id: UUID) -> None:
        """Before alerts are cleared, so a failure leaves the sweep a trail."""
        ...

    async def move_occurrence(
        self,
        *,
        user_id: UUID,
        event_id: UUID,
        schedule: LocalSchedule,
        starts_at: datetime,
        ends_at: datetime,
    ) -> StoredEventDTO | None:
        """A yearly roll or a timezone change: new local fields or zone and
        instants, alerts pending. None when the event is gone."""
        ...

    async def select_yearly_to_roll(
        self, *, now: datetime, limit: int
    ) -> list[EventTargetDTO]:
        """Every user's live yearly events whose stored occurrence has ended
        (build plan AD-4). Service role."""
        ...

    async def select_alerts_pending(
        self, *, updated_before: datetime, limit: int
    ) -> list[EventTargetDTO]:
        """Every user's live events whose alerts are still pending since
        before ``updated_before``. Service role."""
        ...

    async def count_alerts_pending(self, *, updated_before: datetime) -> int:
        """NFR-4's count of events whose alerts are out of step."""
        ...

    async def search_events(
        self,
        *,
        user_id: UUID,
        terms: Sequence[str],
        query_embedding: Sequence[float] | None,
        max_distance: float,
        limit: int,
    ) -> StoredEventSearchPageDTO:
        """Live events matching any term or within ``max_distance``, cut at
        ``limit`` in the database's own order; search ranks (005 AD-3)."""
        ...

    async def get_embedding(
        self, *, user_id: UUID, event_id: UUID
    ) -> tuple[float, ...] | None: ...

    async def get_text_needing_embedding(
        self, *, user_id: UUID, event_id: UUID
    ) -> EventText | None:
        """The live event's words while it has no vector, else None."""
        ...

    async def set_embedding(
        self,
        *,
        user_id: UUID,
        event_id: UUID,
        words: EventText,
        embedding: Sequence[float],
    ) -> bool:
        """Store the vector only while the words are still ``words``."""
        ...

    async def select_missing_embeddings(
        self,
        *,
        updated_since: datetime | None,
        after_id: UUID | None,
        limit: int,
    ) -> list[EventTargetDTO]:
        """Every user's live events with no vector. Service role."""
        ...
