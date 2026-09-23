"""The only SQL in the reminders domain. Returns DTOs, never models."""

import uuid
from datetime import UTC, datetime
from typing import cast
from zoneinfo import ZoneInfo

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import user_transaction
from app.domains.reminders.interfaces.dtos import (
    DueReminderDTO,
    FiringDTO,
    LatenessValue,
    RecordOriginValue,
    ReminderActionValue,
    ReminderDTO,
    ReminderStateValue,
    UserActionValue,
)
from app.domains.reminders.interfaces.repositories import (
    FiringWrite,
    RecordedFiring,
    ReminderStateWrite,
    ReminderWrite,
)
from app.domains.reminders.models import Reminder, ReminderFiring
from app.domains.reminders.services.firing import summarize_reminder
from app.domains.reminders.services.schedule import RepeatKind, ScheduleSpec


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
                .values(
                    deleted_at=now,
                    updated_at=now,
                    next_fire_at=None,
                    snoozed_until=None,
                )
                .returning(Reminder.id)
            )
            deleted_id = result.scalar_one_or_none()
        return deleted_id is not None

    async def select_due(self, *, now: datetime, limit: int) -> list[DueReminderDTO]:
        # No user_transaction: the sweep reads every user's rows on the
        # service-role connection, as a background job may (T3).
        due_at = func.least(Reminder.next_fire_at, Reminder.snoozed_until)
        async with self.session.begin():
            rows = (
                await self.session.execute(
                    select(Reminder.id, due_at)
                    .where(
                        Reminder.deleted_at.is_(None),
                        Reminder.state != "done",
                        due_at <= now,
                    )
                    .order_by(due_at)
                    .limit(limit)
                )
            ).all()
        return [DueReminderDTO(reminder_id=row[0], due_at=row[1]) for row in rows]

    async def get_for_firing(self, *, reminder_id: uuid.UUID) -> ReminderDTO | None:
        now = datetime.now(UTC)
        async with self.session.begin():
            reminder = await self.session.scalar(
                select(Reminder).where(
                    Reminder.id == reminder_id,
                    Reminder.deleted_at.is_(None),
                    Reminder.state != "done",
                )
            )
        if reminder is None:
            return None
        return _reminder_to_dto(reminder=reminder, now=now)

    async def record_firing(
        self,
        *,
        user_id: uuid.UUID,
        reminder_id: uuid.UUID,
        expected_due_at: datetime,
        firing: FiringWrite,
        state: ReminderStateWrite,
    ) -> RecordedFiring | None:
        async with user_transaction(self.session, user_id) as scoped:
            reminder = await scoped.scalar(
                select(Reminder)
                .where(
                    Reminder.id == reminder_id,
                    Reminder.user_id == user_id,
                    Reminder.deleted_at.is_(None),
                    Reminder.state != "done",
                )
                .with_for_update()
            )
            if reminder is None or _due_at(reminder=reminder) != expected_due_at:
                return None
            firing_id = await scoped.scalar(
                insert(ReminderFiring)
                .values(
                    id=uuid.uuid4(),
                    reminder_id=reminder_id,
                    user_id=user_id,
                    scheduled_for=firing.scheduled_for,
                    fired_at=firing.fired_at,
                    lateness=firing.lateness,
                )
                .on_conflict_do_nothing(index_elements=["reminder_id", "scheduled_for"])
                .returning(ReminderFiring.id)
            )
            is_new = firing_id is not None
            if is_new:
                await scoped.execute(
                    update(Reminder)
                    .where(Reminder.id == reminder_id)
                    .values(updated_at=firing.fired_at, **_state_columns(state=state))
                )
            stored = (
                await scoped.scalars(
                    select(ReminderFiring).where(
                        ReminderFiring.reminder_id == reminder_id,
                        ReminderFiring.scheduled_for == firing.scheduled_for,
                    )
                )
            ).one()
        return RecordedFiring(firing=_firing_to_dto(firing=stored), is_new=is_new)

    async def get_latest_firing(
        self, *, user_id: uuid.UUID, reminder_id: uuid.UUID
    ) -> FiringDTO | None:
        async with user_transaction(self.session, user_id) as scoped:
            firing = await scoped.scalar(
                select(ReminderFiring)
                .where(
                    ReminderFiring.reminder_id == reminder_id,
                    ReminderFiring.user_id == user_id,
                )
                .order_by(ReminderFiring.fired_at.desc())
                .limit(1)
            )
        return _firing_to_dto(firing=firing) if firing is not None else None

    async def record_action(
        self,
        *,
        user_id: uuid.UUID,
        reminder_id: uuid.UUID,
        firing_id: uuid.UUID | None,
        action: UserActionValue,
        acted_at: datetime,
        state: ReminderStateWrite,
    ) -> ReminderDTO | None:
        async with user_transaction(self.session, user_id) as scoped:
            result = await scoped.execute(
                update(Reminder)
                .where(
                    Reminder.id == reminder_id,
                    Reminder.user_id == user_id,
                    Reminder.deleted_at.is_(None),
                )
                .values(updated_at=acted_at, **_state_columns(state=state))
                .returning(Reminder)
            )
            reminder = result.scalar_one_or_none()
            if reminder is not None and firing_id is not None:
                await scoped.execute(
                    update(ReminderFiring)
                    .where(
                        ReminderFiring.id == firing_id,
                        ReminderFiring.user_id == user_id,
                    )
                    .values(action=action, acted_at=acted_at)
                )
        if reminder is None:
            return None
        return _reminder_to_dto(reminder=reminder, now=acted_at)


def _due_at(*, reminder: Reminder) -> datetime | None:
    instants = [
        instant
        for instant in (reminder.next_fire_at, reminder.snoozed_until)
        if instant is not None
    ]
    return min(instants) if instants else None


def _state_columns(*, state: ReminderStateWrite) -> dict[str, object]:
    return {
        "state": state.state,
        "next_fire_at": state.next_fire_at,
        "snoozed_until": state.snoozed_until,
        "last_fired_at": state.last_fired_at,
        "last_action": state.last_action,
    }


def _firing_to_dto(*, firing: ReminderFiring) -> FiringDTO:
    return FiringDTO(
        id=firing.id,
        reminder_id=firing.reminder_id,
        user_id=firing.user_id,
        scheduled_for=firing.scheduled_for,
        fired_at=firing.fired_at,
        lateness=cast(LatenessValue, firing.lateness),
        action=cast(ReminderActionValue | None, firing.action),
        acted_at=firing.acted_at,
    )


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
        # An edit replaces the series; a pending snooze belonged to the old one.
        "snoozed_until": None,
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
        # Wording only, from the pure firing module: no rule is decided here.
        summary=summarize_reminder(
            spec=spec,
            timezone=ZoneInfo(reminder.schedule_timezone),
            now=now,
            state=cast(ReminderStateValue, reminder.state),
            last_fired_at=reminder.last_fired_at,
            last_action=cast(ReminderActionValue | None, reminder.last_action),
            snoozed_until=reminder.snoozed_until,
        ),
        origin=cast(RecordOriginValue, reminder.origin),
        original_input=reminder.original_input,
        created_at=reminder.created_at,
        updated_at=reminder.updated_at,
        snoozed_until=reminder.snoozed_until,
    )
