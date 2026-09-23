"""FR-21: fire again in 10 minutes, in an hour, or tomorrow at the default
time. A one-off extra firing: the series keeps its schedule (4.2 decision 1)."""

from collections.abc import Callable
from datetime import datetime
from zoneinfo import ZoneInfo

from app.domains.reminders.graphql.errors import ReminderNotFoundError
from app.domains.reminders.interactors.dtos import SnoozeReminderInputDTO
from app.domains.reminders.interfaces.dtos import ReminderDTO
from app.domains.reminders.interfaces.ports import NotificationPort, UserClockPort
from app.domains.reminders.interfaces.repositories import (
    ReminderRepository,
    ReminderStateWrite,
)
from app.domains.reminders.services.firing import snooze_instant


class SnoozeReminderInteractor:
    def __init__(
        self,
        *,
        reminder_repository: ReminderRepository,
        notifications: NotificationPort,
        user_clock: UserClockPort,
        now_provider: Callable[[], datetime],
    ) -> None:
        self.reminder_repository = reminder_repository
        self.notifications = notifications
        self.user_clock = user_clock
        self.now_provider = now_provider

    async def snooze_reminder(self, *, dto: SnoozeReminderInputDTO) -> ReminderDTO:
        """Raises:
        ReminderNotFoundError: no live reminder with this id is theirs.
        """
        reminder = await self._get_owned_reminder(dto=dto)
        now = self.now_provider()
        clock = await self.user_clock.get_user_clock(user_id=dto.user_id)
        snoozed_until = snooze_instant(
            option=dto.option,
            now=now,
            timezone=ZoneInfo(reminder.schedule_timezone),
            default_time=clock.default_reminder_time,
        )
        firing = await self.reminder_repository.get_latest_firing(
            user_id=dto.user_id, reminder_id=dto.reminder_id
        )
        updated = await self.reminder_repository.record_action(
            user_id=dto.user_id,
            reminder_id=dto.reminder_id,
            firing_id=firing.id if firing is not None else None,
            action="snoozed",
            acted_at=now,
            state=ReminderStateWrite(
                state="upcoming",
                next_fire_at=reminder.next_fire_at,
                snoozed_until=snoozed_until,
                last_fired_at=reminder.last_fired_at,
                last_action="snoozed",
            ),
        )
        if updated is None:
            raise ReminderNotFoundError()
        if firing is not None:
            await self.notifications.record_action(
                user_id=dto.user_id, firing_id=firing.id, action="snoozed", acted_at=now
            )
        return updated

    async def _get_owned_reminder(self, *, dto: SnoozeReminderInputDTO) -> ReminderDTO:
        reminder = await self.reminder_repository.get_by_id(
            user_id=dto.user_id, reminder_id=dto.reminder_id
        )
        if reminder is None:
            raise ReminderNotFoundError()
        return reminder
