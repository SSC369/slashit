"""The only SQL in the reminders domain. Returns DTOs, never models."""

import uuid
from datetime import UTC, datetime
from typing import cast
from zoneinfo import ZoneInfo

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import user_transaction
from app.domains.reminders.interfaces.dtos import (
    RecordOriginValue,
    ReminderActionValue,
    ReminderDTO,
    ReminderStateValue,
)
from app.domains.reminders.interfaces.repositories import ReminderWrite
from app.domains.reminders.models import Reminder
from app.domains.reminders.services.schedule import (
    RepeatKind,
    ScheduleSpec,
    describe,
)


class SqlReminderRepository:
    """Reads and writes ``reminders`` against the request's own session."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_reminder(
        self,
        *,
        user_id: uuid.UUID,
        write: ReminderWrite,
        origin: RecordOriginValue,
        original_input: str | None,
    ) -> ReminderDTO:
        now = datetime.now(UTC)
        reminder = Reminder(
            id=uuid.uuid4(),
            user_id=user_id,
            origin=origin,
            original_input=original_input,
            created_at=now,
            updated_at=now,
            last_fired_at=None,
            last_action=None,
            deleted_at=None,
            **_write_columns(write=write),
        )
        async with user_transaction(self.session, user_id) as scoped:
            scoped.add(reminder)
        return _reminder_to_dto(reminder=reminder, now=now)

    async def count_active_for_user(self, *, user_id: uuid.UUID) -> int:
        async with user_transaction(self.session, user_id) as scoped:
            count = await scoped.scalar(
                select(func.count())
                .select_from(Reminder)
                .where(
                    Reminder.user_id == user_id,
                    Reminder.deleted_at.is_(None),
                    Reminder.state != "done",
                )
            )
        return int(count or 0)

    async def list_for_user(
        self, *, user_id: uuid.UUID, search: str | None
    ) -> list[ReminderDTO]:
        now = datetime.now(UTC)
        statement = select(Reminder).where(
            Reminder.user_id == user_id, Reminder.deleted_at.is_(None)
        )
        if search:
            statement = statement.where(Reminder.description.ilike(f"%{search}%"))
        async with user_transaction(self.session, user_id) as scoped:
            reminders = (await scoped.scalars(statement)).all()
        return [_reminder_to_dto(reminder=reminder, now=now) for reminder in reminders]

    async def get_by_id(
        self, *, user_id: uuid.UUID, reminder_id: uuid.UUID
    ) -> ReminderDTO | None:
        now = datetime.now(UTC)
        async with user_transaction(self.session, user_id) as scoped:
            reminder = await scoped.get(Reminder, reminder_id)
        if (
            reminder is None
            or reminder.user_id != user_id
            or reminder.deleted_at is not None
        ):
            return None
        return _reminder_to_dto(reminder=reminder, now=now)

    async def is_deleted(self, *, user_id: uuid.UUID, reminder_id: uuid.UUID) -> bool:
        async with user_transaction(self.session, user_id) as scoped:
            reminder = await scoped.get(Reminder, reminder_id)
        return (
            reminder is not None
            and reminder.user_id == user_id
            and reminder.deleted_at is not None
        )

    async def update_series(
        self, *, user_id: uuid.UUID, reminder_id: uuid.UUID, write: ReminderWrite
    ) -> ReminderDTO | None:
        now = datetime.now(UTC)
        async with user_transaction(self.session, user_id) as scoped:
            result = await scoped.execute(
                update(Reminder)
                .where(
                    Reminder.id == reminder_id,
                    Reminder.user_id == user_id,
                    Reminder.deleted_at.is_(None),
                )
                .values(updated_at=now, **_write_columns(write=write))
                .returning(Reminder)
            )
            reminder = result.scalar_one_or_none()
        if reminder is None:
            return None
        return _reminder_to_dto(reminder=reminder, now=now)

    async def soft_delete(self, *, user_id: uuid.UUID, reminder_id: uuid.UUID) -> bool:
        now = datetime.now(UTC)
        async with user_transaction(self.session, user_id) as scoped:
            result = await scoped.execute(
                update(Reminder)
                .where(
                    Reminder.id == reminder_id,
                    Reminder.user_id == user_id,
                    Reminder.deleted_at.is_(None),
                )
                .values(deleted_at=now, updated_at=now, next_fire_at=None)
                .returning(Reminder.id)
            )
            deleted_id = result.scalar_one_or_none()
        return deleted_id is not None


def _write_columns(*, write: ReminderWrite) -> dict[str, object]:
    spec = write.spec
    return {
        "description": write.description,
        "repeat_kind": spec.repeat_kind.value,
        "repeat_interval": spec.repeat_interval,
        "repeat_weekdays": list(spec.repeat_weekdays),
        "repeat_month_day": spec.repeat_month_day,
        "local_time": spec.local_time,
        "anchor_local_date": spec.anchor_local_date,
        "one_time_at": spec.one_time_at,
        "next_fire_at": write.next_fire_at,
        "schedule_timezone": write.schedule_timezone,
        "state": write.state,
    }


def _reminder_to_dto(*, reminder: Reminder, now: datetime) -> ReminderDTO:
    spec = ScheduleSpec(
        repeat_kind=RepeatKind(reminder.repeat_kind),
        repeat_interval=reminder.repeat_interval,
        repeat_weekdays=tuple(reminder.repeat_weekdays),
        repeat_month_day=reminder.repeat_month_day,
        local_time=reminder.local_time,
        anchor_local_date=reminder.anchor_local_date,
        one_time_at=reminder.one_time_at,
    )
    return ReminderDTO(
        id=reminder.id,
        user_id=reminder.user_id,
        description=reminder.description,
        spec=spec,
        schedule_timezone=reminder.schedule_timezone,
        next_fire_at=reminder.next_fire_at,
        state=cast(ReminderStateValue, reminder.state),
        last_fired_at=reminder.last_fired_at,
        last_action=cast(ReminderActionValue | None, reminder.last_action),
        # Wording only, from the pure schedule module: no rule is decided here.
        summary=describe(
            spec=spec, timezone=ZoneInfo(reminder.schedule_timezone), now=now
        ),
        origin=cast(RecordOriginValue, reminder.origin),
        original_input=reminder.original_input,
        created_at=reminder.created_at,
        updated_at=reminder.updated_at,
    )
