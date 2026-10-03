"""An in-memory EventRepository for the events domain's calendar_events."""

import uuid
from dataclasses import replace
from datetime import UTC, datetime

from app.domains.events.interfaces.dtos import (
    EventLimitReached,
    EventWrite,
    StoredEventDTO,
)


class FakeCalendarEventRepository:
    def __init__(self) -> None:
        self.rows: list[StoredEventDTO] = []
        self.deleted_ids: set[uuid.UUID] = set()

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

    async def set_alert_leads(
        self, *, user_id: uuid.UUID, event_id: uuid.UUID, leads: tuple[int, ...]
    ) -> None:
        self.rows = [
            replace(row, alert_leads_minutes=leads)
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
        updated = replace(
            existing,
            title=write.title,
            location=write.location,
            description=write.description,
            schedule=write.schedule,
            starts_at=write.starts_at,
            ends_at=write.ends_at,
            alert_leads_minutes=write.alert_leads_minutes,
            updated_at=datetime.now(UTC),
        )
        self.rows = [updated if row.id == event_id else row for row in self.rows]
        return updated

    async def soft_delete(self, *, user_id: uuid.UUID, event_id: uuid.UUID) -> bool:
        if await self.get_by_id(user_id=user_id, event_id=event_id) is None:
            return False
        self.deleted_ids.add(event_id)
        return True
