"""An in-memory EventRepository for the events domain's calendar_events."""

import uuid
from collections.abc import Sequence
from dataclasses import replace
from datetime import UTC, datetime

from app.domains.events.interfaces.dtos import (
    EventLimitReached,
    EventTargetDTO,
    EventText,
    EventWrite,
    StoredEventDTO,
    StoredEventSearchPageDTO,
)
from app.domains.events.services.schedule import LocalSchedule


class FakeCalendarEventRepository:
    def __init__(self) -> None:
        self.rows: list[StoredEventDTO] = []
        self.deleted_ids: set[uuid.UUID] = set()
        self.embeddings: dict[uuid.UUID, tuple[float, ...]] = {}

    async def create_event_if_upcoming_below(
        self, *, user_id: uuid.UUID, write: EventWrite, limit: int, now: datetime
    ) -> StoredEventDTO | None:
        upcoming = [
            row
            for row in self.rows
            if row.user_id == user_id
            and row.id not in self.deleted_ids
            and (row.schedule.repeat_yearly or row.ends_at > now)
        ]
        if len(upcoming) >= limit:
            return None
        created_at = datetime.now(UTC)
        stored = StoredEventDTO(
            id=uuid.uuid4(),
            user_id=user_id,
            title=write.title,
            location=write.location,
            description=write.description,
            schedule=write.schedule,
            starts_at=write.starts_at,
            ends_at=write.ends_at,
            alert_leads_minutes=write.alert_leads_minutes,
            origin=write.origin,
            original_input=write.original_input,
            created_at=created_at,
            updated_at=created_at,
            alerts_pending=write.alerts_pending,
        )
        self.rows.append(stored)
        return stored

    async def list_for_user(self, *, user_id: uuid.UUID) -> list[StoredEventDTO]:
        return [
            row
            for row in self.rows
            if row.user_id == user_id and row.id not in self.deleted_ids
        ]

    async def get_by_id(
        self, *, user_id: uuid.UUID, event_id: uuid.UUID
    ) -> StoredEventDTO | None:
        for row in await self.list_for_user(user_id=user_id):
            if row.id == event_id:
                return row
        return None

    async def finish_arming(
        self, *, user_id: uuid.UUID, event_id: uuid.UUID, leads: tuple[int, ...]
    ) -> None:
        self._replace_row(
            user_id=user_id,
            event_id=event_id,
            alert_leads_minutes=leads,
            alerts_pending=False,
        )

    async def mark_alerts_pending(
        self, *, user_id: uuid.UUID, event_id: uuid.UUID
    ) -> None:
        self._replace_row(user_id=user_id, event_id=event_id, alerts_pending=True)

    async def move_occurrence(
        self,
        *,
        user_id: uuid.UUID,
        event_id: uuid.UUID,
        schedule: LocalSchedule,
        starts_at: datetime,
        ends_at: datetime,
    ) -> StoredEventDTO | None:
        if await self.get_by_id(user_id=user_id, event_id=event_id) is None:
            return None
        self._replace_row(
            user_id=user_id,
            event_id=event_id,
            schedule=schedule,
            starts_at=starts_at,
            ends_at=ends_at,
            alerts_pending=True,
        )
        return await self.get_by_id(user_id=user_id, event_id=event_id)

    async def select_yearly_to_roll(
        self, *, now: datetime, limit: int
    ) -> list[EventTargetDTO]:
        return [
            EventTargetDTO(user_id=row.user_id, event_id=row.id)
            for row in self._live()
            if row.schedule.repeat_yearly and row.ends_at <= now
        ][:limit]

    async def select_alerts_pending(
        self, *, updated_before: datetime, limit: int
    ) -> list[EventTargetDTO]:
        return [
            EventTargetDTO(user_id=row.user_id, event_id=row.id)
            for row in self._live()
            if row.alerts_pending and row.updated_at < updated_before
        ][:limit]

    async def count_alerts_pending(self, *, updated_before: datetime) -> int:
        return len(
            await self.select_alerts_pending(
                updated_before=updated_before, limit=len(self.rows)
            )
        )

    def _live(self) -> list[StoredEventDTO]:
        return [row for row in self.rows if row.id not in self.deleted_ids]

    def _replace_row(
        self, *, user_id: uuid.UUID, event_id: uuid.UUID, **changes: object
    ) -> None:
        self.rows = [
            replace(row, **changes)  # type: ignore[arg-type]
            if row.id == event_id and row.user_id == user_id
            else row
            for row in self.rows
        ]

    async def update_event_if_upcoming_below(
        self,
        *,
        user_id: uuid.UUID,
        event_id: uuid.UUID,
        write: EventWrite,
        limit: int,
        now: datetime,
    ) -> StoredEventDTO | EventLimitReached | None:
        existing = await self.get_by_id(user_id=user_id, event_id=event_id)
        if existing is None:
            return None
        other_upcoming = [
            row
            for row in await self.list_for_user(user_id=user_id)
            if row.id != event_id and (row.schedule.repeat_yearly or row.ends_at > now)
        ]
        becomes_upcoming = write.schedule.repeat_yearly or write.ends_at > now
        if becomes_upcoming and len(other_upcoming) >= limit:
            return EventLimitReached(limit=limit)
        if (existing.title, existing.location, existing.description) != (
            write.title,
            write.location,
            write.description,
        ):
            self.embeddings.pop(event_id, None)
        updated = replace(
            existing,
            title=write.title,
            location=write.location,
            description=write.description,
            schedule=write.schedule,
            starts_at=write.starts_at,
            ends_at=write.ends_at,
            alert_leads_minutes=write.alert_leads_minutes,
            alerts_pending=write.alerts_pending,
            updated_at=datetime.now(UTC),
        )
        self.rows = [updated if row.id == event_id else row for row in self.rows]
        return updated

    async def soft_delete(self, *, user_id: uuid.UUID, event_id: uuid.UUID) -> bool:
        if await self.get_by_id(user_id=user_id, event_id=event_id) is None:
            return False
        self.deleted_ids.add(event_id)
        return True

    async def search_events(
        self,
        *,
        user_id: uuid.UUID,
        terms: Sequence[str],
        query_embedding: Sequence[float] | None,
        max_distance: float,
        limit: int,
    ) -> StoredEventSearchPageDTO:
        raise NotImplementedError("search runs against PostgreSQL in its tests")

    async def get_embedding(
        self, *, user_id: uuid.UUID, event_id: uuid.UUID
    ) -> tuple[float, ...] | None:
        if await self.get_by_id(user_id=user_id, event_id=event_id) is None:
            return None
        return self.embeddings.get(event_id)

    async def get_text_needing_embedding(
        self, *, user_id: uuid.UUID, event_id: uuid.UUID
    ) -> EventText | None:
        row = await self.get_by_id(user_id=user_id, event_id=event_id)
        if row is None or event_id in self.embeddings:
            return None
        return EventText(
            title=row.title, location=row.location, description=row.description
        )

    async def set_embedding(
        self,
        *,
        user_id: uuid.UUID,
        event_id: uuid.UUID,
        words: EventText,
        embedding: Sequence[float],
    ) -> bool:
        current = await self.get_text_needing_embedding(
            user_id=user_id, event_id=event_id
        )
        if current != words:
            return False
        self.embeddings[event_id] = tuple(embedding)
        return True

    async def select_missing_embeddings(
        self,
        *,
        updated_since: datetime | None,
        after_id: uuid.UUID | None,
        limit: int,
    ) -> list[EventTargetDTO]:
        missing = sorted(
            (
                row
                for row in self._live()
                if row.id not in self.embeddings
                and (updated_since is None or row.updated_at >= updated_since)
                and (after_id is None or row.id > after_id)
            ),
            key=lambda row: row.id,
        )
        return [
            EventTargetDTO(user_id=row.user_id, event_id=row.id) for row in missing
        ][:limit]
