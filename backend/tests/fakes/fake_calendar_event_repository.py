"""An in-memory EventRepository for the events domain's calendar_events."""

import uuid
from datetime import UTC, datetime

from app.domains.events.interfaces.dtos import EventWrite, StoredEventDTO


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
            alert_lead_minutes=write.alert_lead_minutes,
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
