"""Create one reminder from what a sentence said. FR-1 to FR-4, FR-38."""

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime
from uuid import UUID

from app.domains.reminders.constants import (
    MAX_ACTIVE_REMINDERS,
    MAX_REPEAT_INTERVAL,
    MIN_REPEAT_INTERVAL,
)
from app.domains.reminders.interfaces.dtos import (
    RecordOriginValue,
    ReminderDTO,
    ReminderFields,
    ReminderLimitReached,
    ReminderNeedsWhen,
)
from app.domains.reminders.interfaces.ports import UserClockPort
from app.domains.reminders.interfaces.repositories import (
    ReminderRepository,
    ReminderWrite,
)
from app.domains.reminders.services.schedule_planner import plan_schedule

CreateReminderOutcome = ReminderDTO | ReminderLimitReached | ReminderNeedsWhen


class CreateReminderInteractor:
    def __init__(
        self,
        *,
        reminder_repository: ReminderRepository,
        user_clock: UserClockPort,
        now_provider: Callable[[], datetime],
    ) -> None:
        self.reminder_repository = reminder_repository
        self.user_clock = user_clock
        self.now_provider = now_provider

    async def create_reminder(
        self,
        *,
        user_id: UUID,
        fields: ReminderFields,
        origin: RecordOriginValue,
        original_input: str | None,
    ) -> CreateReminderOutcome:
        """Plan the schedule and store the reminder.

        Returns ``ReminderLimitReached`` at the cap and ``ReminderNeedsWhen``
        when no date was given that the rule can start from. Neither writes.
        Both are outcomes a capture renders, not errors, so nothing raises.
        """
        if await self._is_at_active_limit(user_id=user_id):
            return ReminderLimitReached(limit=MAX_ACTIVE_REMINDERS)

        clock = await self.user_clock.get_user_clock(user_id=user_id)
        planned = plan_schedule(
            fields=self._normalise_fields(fields=fields),
            clock=clock,
            now=self.now_provider(),
        )
        if planned is None:
            return ReminderNeedsWhen(description=fields.description.strip())

        created = await self.reminder_repository.create_reminder(
            user_id=user_id,
            write=ReminderWrite(
                description=fields.description.strip(),
                spec=planned.spec,
                schedule_timezone=clock.timezone,
                next_fire_at=planned.next_fire_at,
                state="upcoming",
            ),
            origin=origin,
            original_input=original_input,
        )
        return replace(created, when_note=planned.when_note)

    async def _is_at_active_limit(self, *, user_id: UUID) -> bool:
        active_count = await self.reminder_repository.count_active_for_user(
            user_id=user_id
        )
        return active_count >= MAX_ACTIVE_REMINDERS

    def _normalise_fields(self, *, fields: ReminderFields) -> ReminderFields:
        """A model's stray values become the nearest legal ones rather than an
        error the user cannot fix: an interval of 0 means every, an unknown
        weekday is dropped."""
        interval = min(
            max(fields.repeat_interval, MIN_REPEAT_INTERVAL), MAX_REPEAT_INTERVAL
        )
        weekdays = tuple(day for day in fields.repeat_weekdays if 0 <= day <= 6)
        month_day = (
            fields.month_day
            if fields.month_day and 1 <= fields.month_day <= 31
            else None
        )
        return replace(
            fields,
            repeat_interval=interval,
            repeat_weekdays=weekdays,
            month_day=month_day,
        )
