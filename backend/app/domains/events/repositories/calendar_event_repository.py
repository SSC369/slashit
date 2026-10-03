"""The only SQL in the events domain. Returns DTOs, never models."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import user_transaction
from app.domains.events.interfaces.dtos import (
    EventWrite,
    RecordOriginValue,
    StoredEventDTO,
)
from app.domains.events.models import CalendarEvent
from app.domains.events.services.schedule import LocalSchedule


class SqlCalendarEventRepository:
    """Reads and writes ``calendar_events`` against the request's own session."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_event_if_upcoming_below(
        self, *, user_id: uuid.UUID, write: EventWrite, limit: int, now: datetime
    ) -> StoredEventDTO | None:
        created_at = datetime.now(UTC)
        event = CalendarEvent(
            id=uuid.uuid4(),
            user_id=user_id,
            title=write.title,
            location=write.location,
            description=write.description,
            start_date=write.schedule.start_date,
            start_time=write.schedule.start_time,
            end_date=write.schedule.end_date,
            end_time=write.schedule.end_time,
            repeat_yearly=write.schedule.repeat_yearly,
            schedule_timezone=write.schedule.timezone,
            starts_at=write.starts_at,
            ends_at=write.ends_at,
            alert_leads_minutes=list(write.alert_leads_minutes),
            origin=write.origin,
            original_input=write.original_input,
            created_at=created_at,
            updated_at=created_at,
            deleted_at=None,
        )
        async with user_transaction(self.session, user_id) as scoped:
            # Serialises this user's creates for the rest of the transaction.
            await scoped.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:key))"),
                {"key": f"calendar_events:{user_id}"},
            )
            upcoming_count = await scoped.scalar(
                select(func.count())
                .select_from(CalendarEvent)
                .where(
                    CalendarEvent.user_id == user_id,
                    CalendarEvent.deleted_at.is_(None),
                    or_(CalendarEvent.repeat_yearly, CalendarEvent.ends_at > now),
                )
            )
            if int(upcoming_count or 0) >= limit:
                return None
            scoped.add(event)
        return _event_to_dto(event=event)

    async def list_for_user(self, *, user_id: uuid.UUID) -> list[StoredEventDTO]:
        statement = select(CalendarEvent).where(
            CalendarEvent.user_id == user_id, CalendarEvent.deleted_at.is_(None)
        )
        async with user_transaction(self.session, user_id) as scoped:
            events = (await scoped.scalars(statement)).all()
        return [_event_to_dto(event=event) for event in events]

    async def get_by_id(
        self, *, user_id: uuid.UUID, event_id: uuid.UUID
    ) -> StoredEventDTO | None:
        async with user_transaction(self.session, user_id) as scoped:
            event = await scoped.get(CalendarEvent, event_id)
        if event is None or event.user_id != user_id or event.deleted_at is not None:
            return None
        return _event_to_dto(event=event)


def _event_to_dto(*, event: CalendarEvent) -> StoredEventDTO:
    origin: RecordOriginValue = "edit" if event.origin == "edit" else "command"
    return StoredEventDTO(
        id=event.id,
        user_id=event.user_id,
        title=event.title,
        location=event.location,
        description=event.description,
        schedule=LocalSchedule(
            start_date=event.start_date,
            start_time=event.start_time,
            end_date=event.end_date,
            end_time=event.end_time,
            repeat_yearly=event.repeat_yearly,
            timezone=event.schedule_timezone,
        ),
        starts_at=event.starts_at,
        ends_at=event.ends_at,
        alert_leads_minutes=tuple(event.alert_leads_minutes),
        origin=origin,
        original_input=event.original_input,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )
