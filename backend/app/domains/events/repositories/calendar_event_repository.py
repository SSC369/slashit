"""The only SQL in the events domain. Returns DTOs, never models."""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import CursorResult, Update, func, or_, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import user_transaction
from app.core.text_search import build_search_expressions
from app.domains.events.interfaces.dtos import (
    EventLimitReached,
    EventTargetDTO,
    EventText,
    EventWrite,
    RecordOriginValue,
    StoredEventDTO,
    StoredEventMatchDTO,
    StoredEventSearchPageDTO,
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
            alerts_pending=write.alerts_pending,
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

    async def update_event_if_upcoming_below(
        self,
        *,
        user_id: uuid.UUID,
        event_id: uuid.UUID,
        write: EventWrite,
        limit: int,
        now: datetime,
    ) -> StoredEventDTO | EventLimitReached | None:
        async with user_transaction(self.session, user_id) as scoped:
            await scoped.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:key))"),
                {"key": f"calendar_events:{user_id}"},
            )
            event = await scoped.get(CalendarEvent, event_id)
            if (
                event is None
                or event.user_id != user_id
                or event.deleted_at is not None
            ):
                return None
            other_upcoming = await scoped.scalar(
                select(func.count())
                .select_from(CalendarEvent)
                .where(
                    CalendarEvent.user_id == user_id,
                    CalendarEvent.id != event_id,
                    CalendarEvent.deleted_at.is_(None),
                    or_(CalendarEvent.repeat_yearly, CalendarEvent.ends_at > now),
                )
            )
            becomes_upcoming = write.schedule.repeat_yearly or write.ends_at > now
            if becomes_upcoming and int(other_upcoming or 0) >= limit:
                return EventLimitReached(limit=limit)
            _apply_write(event=event, write=write)
        return _event_to_dto(event=event)

    async def soft_delete(self, *, user_id: uuid.UUID, event_id: uuid.UUID) -> bool:
        now = datetime.now(UTC)
        async with user_transaction(self.session, user_id) as scoped:
            result = await scoped.execute(
                update(CalendarEvent)
                .where(
                    CalendarEvent.id == event_id,
                    CalendarEvent.user_id == user_id,
                    CalendarEvent.deleted_at.is_(None),
                )
                .values(deleted_at=now, updated_at=now)
                .returning(CalendarEvent.id)
            )
            deleted_id = result.scalar_one_or_none()
        return deleted_id is not None

    async def search_events(
        self,
        *,
        user_id: uuid.UUID,
        terms: Sequence[str],
        query_embedding: Sequence[float] | None,
        max_distance: float,
        limit: int,
    ) -> StoredEventSearchPageDTO:
        expressions = build_search_expressions(
            search_vector=CalendarEvent.search_vector,
            embedding=CalendarEvent.embedding,
            terms=terms,
            query_embedding=query_embedding,
            max_distance=max_distance,
        )
        if expressions.matches is None:
            return StoredEventSearchPageDTO(matches=[], total=0)
        live_matches = (
            CalendarEvent.user_id == user_id,
            CalendarEvent.deleted_at.is_(None),
            expressions.matches,
        )
        statement = (
            select(
                CalendarEvent,
                expressions.all_terms,
                expressions.word_rank,
                expressions.distance,
            )
            .where(*live_matches)
            .order_by(*expressions.ordering)
            .limit(limit)
        )
        async with user_transaction(self.session, user_id) as scoped:
            rows = (await scoped.execute(statement)).all()
            total = await scoped.scalar(
                select(func.count()).select_from(CalendarEvent).where(*live_matches)
            )
        return StoredEventSearchPageDTO(
            matches=[
                StoredEventMatchDTO(
                    event=_event_to_dto(event=event),
                    all_terms=bool(all_terms),
                    word_rank=word_rank,
                    distance=distance,
                )
                for event, all_terms, word_rank, distance in rows
            ],
            total=int(total or 0),
        )

    async def get_embedding(
        self, *, user_id: uuid.UUID, event_id: uuid.UUID
    ) -> tuple[float, ...] | None:
        async with user_transaction(self.session, user_id) as scoped:
            embedding = await scoped.scalar(
                select(CalendarEvent.embedding).where(
                    CalendarEvent.id == event_id,
                    CalendarEvent.user_id == user_id,
                    CalendarEvent.deleted_at.is_(None),
                )
            )
        return None if embedding is None else tuple(float(item) for item in embedding)

    async def get_text_needing_embedding(
        self, *, user_id: uuid.UUID, event_id: uuid.UUID
    ) -> EventText | None:
        async with user_transaction(self.session, user_id) as scoped:
            row = (
                await scoped.execute(
                    select(
                        CalendarEvent.title,
                        CalendarEvent.location,
                        CalendarEvent.description,
                    ).where(
                        CalendarEvent.id == event_id,
                        CalendarEvent.user_id == user_id,
                        CalendarEvent.deleted_at.is_(None),
                        CalendarEvent.embedding.is_(None),
                    )
                )
            ).one_or_none()
        if row is None:
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
        async with user_transaction(self.session, user_id) as scoped:
            result = cast(
                CursorResult[Any],
                await scoped.execute(
                    _live_event_update(user_id=user_id, event_id=event_id)
                    .where(
                        CalendarEvent.title == words.title,
                        CalendarEvent.location.is_not_distinct_from(words.location),
                        CalendarEvent.description.is_not_distinct_from(
                            words.description
                        ),
                    )
                    .values(embedding=list(embedding))
                ),
            )
        return result.rowcount > 0

    async def select_missing_embeddings(
        self,
        *,
        updated_since: datetime | None,
        after_id: uuid.UUID | None,
        limit: int,
    ) -> list[EventTargetDTO]:
        statement = select(CalendarEvent.user_id, CalendarEvent.id).where(
            CalendarEvent.embedding.is_(None), CalendarEvent.deleted_at.is_(None)
        )
        if updated_since is not None:
            statement = statement.where(CalendarEvent.updated_at >= updated_since)
        if after_id is not None:
            statement = statement.where(CalendarEvent.id > after_id)
        # No user_transaction: the sweep reads every user's rows on the
        # service-role connection, as a background job may (T3).
        async with self.session.begin():
            rows = (
                await self.session.execute(
                    statement.order_by(CalendarEvent.id).limit(limit)
                )
            ).all()
        return [
            EventTargetDTO(user_id=user_id, event_id=event_id)
            for user_id, event_id in rows
        ]

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

    async def finish_arming(
        self, *, user_id: uuid.UUID, event_id: uuid.UUID, leads: tuple[int, ...]
    ) -> None:
        async with user_transaction(self.session, user_id) as scoped:
            await scoped.execute(
                _live_event_update(user_id=user_id, event_id=event_id).values(
                    alert_leads_minutes=list(leads),
                    alerts_pending=False,
                    updated_at=datetime.now(UTC),
                )
            )

    async def mark_alerts_pending(
        self, *, user_id: uuid.UUID, event_id: uuid.UUID
    ) -> None:
        async with user_transaction(self.session, user_id) as scoped:
            await scoped.execute(
                _live_event_update(user_id=user_id, event_id=event_id).values(
                    alerts_pending=True, updated_at=datetime.now(UTC)
                )
            )

    async def move_occurrence(
        self,
        *,
        user_id: uuid.UUID,
        event_id: uuid.UUID,
        schedule: LocalSchedule,
        starts_at: datetime,
        ends_at: datetime,
    ) -> StoredEventDTO | None:
        async with user_transaction(self.session, user_id) as scoped:
            moved_id = await scoped.scalar(
                _live_event_update(user_id=user_id, event_id=event_id)
                .values(
                    start_date=schedule.start_date,
                    start_time=schedule.start_time,
                    end_date=schedule.end_date,
                    end_time=schedule.end_time,
                    schedule_timezone=schedule.timezone,
                    starts_at=starts_at,
                    ends_at=ends_at,
                    alerts_pending=True,
                    updated_at=datetime.now(UTC),
                )
                .returning(CalendarEvent.id)
            )
        if moved_id is None:
            return None
        return await self.get_by_id(user_id=user_id, event_id=event_id)

    async def select_yearly_to_roll(
        self, *, now: datetime, limit: int
    ) -> list[EventTargetDTO]:
        # No user_transaction: the job reads every user's rows on the service
        # role (T3); each event is then moved in its own user's transaction.
        async with self.session.begin():
            rows = (
                await self.session.execute(
                    select(CalendarEvent.user_id, CalendarEvent.id)
                    .where(
                        CalendarEvent.repeat_yearly,
                        CalendarEvent.deleted_at.is_(None),
                        CalendarEvent.ends_at <= now,
                    )
                    .order_by(CalendarEvent.ends_at)
                    .limit(limit)
                )
            ).all()
        return [
            EventTargetDTO(user_id=user_id, event_id=event_id)
            for user_id, event_id in rows
        ]

    async def select_alerts_pending(
        self, *, updated_before: datetime, limit: int
    ) -> list[EventTargetDTO]:
        async with self.session.begin():
            rows = (
                await self.session.execute(
                    select(CalendarEvent.user_id, CalendarEvent.id)
                    .where(
                        CalendarEvent.alerts_pending,
                        CalendarEvent.deleted_at.is_(None),
                        CalendarEvent.updated_at < updated_before,
                    )
                    .order_by(CalendarEvent.updated_at)
                    .limit(limit)
                )
            ).all()
        return [
            EventTargetDTO(user_id=user_id, event_id=event_id)
            for user_id, event_id in rows
        ]

    async def count_alerts_pending(self, *, updated_before: datetime) -> int:
        async with self.session.begin():
            count = await self.session.scalar(
                select(func.count())
                .select_from(CalendarEvent)
                .where(
                    CalendarEvent.alerts_pending,
                    CalendarEvent.deleted_at.is_(None),
                    CalendarEvent.updated_at < updated_before,
                )
            )
        return int(count or 0)


def _live_event_update(*, user_id: uuid.UUID, event_id: uuid.UUID) -> Update:
    return update(CalendarEvent).where(
        CalendarEvent.id == event_id,
        CalendarEvent.user_id == user_id,
        CalendarEvent.deleted_at.is_(None),
    )


def _apply_write(*, event: CalendarEvent, write: EventWrite) -> None:
    """An edit replaces every column the form holds (FR-28). The origin and
    the typed command stay: they say how the event began. Changed words make
    the vector stale, so it is cleared for the embed job (005 AD-7)."""
    words_changed = (event.title, event.location, event.description) != (
        write.title,
        write.location,
        write.description,
    )
    if words_changed:
        event.embedding = None
    event.title = write.title
    event.location = write.location
    event.description = write.description
    event.start_date = write.schedule.start_date
    event.start_time = write.schedule.start_time
    event.end_date = write.schedule.end_date
    event.end_time = write.schedule.end_time
    event.repeat_yearly = write.schedule.repeat_yearly
    event.schedule_timezone = write.schedule.timezone
    event.starts_at = write.starts_at
    event.ends_at = write.ends_at
    event.alert_leads_minutes = list(write.alert_leads_minutes)
    event.alerts_pending = write.alerts_pending
    event.updated_at = datetime.now(UTC)


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
        alerts_pending=event.alerts_pending,
        origin=origin,
        original_input=event.original_input,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )
