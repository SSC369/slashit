"""FR-19, FR-20: Done closes a one-time reminder, or one occurrence of a
recurring one, which stays active for its next."""

from collections.abc import Callable
from datetime import datetime

from app.domains.reminders.graphql.errors import ReminderNotFoundError
from app.domains.reminders.interactors.dtos import MarkReminderDoneInputDTO
from app.domains.reminders.interfaces.dtos import ReminderDTO
from app.domains.reminders.interfaces.ports import NotificationPort
from app.domains.reminders.interfaces.repositories import (
    ReminderRepository,
    ReminderStateWrite,
)
from app.domains.reminders.services.schedule import RepeatKind


class MarkReminderDoneInteractor:
    def __init__(
        self,
        *,
        reminder_repository: ReminderRepository,
        notifications: NotificationPort,
        now_provider: Callable[[], datetime],
    ) -> None:
        self.reminder_repository = reminder_repository
        self.notifications = notifications
        self.now_provider = now_provider

    async def mark_reminder_done(self, *, dto: MarkReminderDoneInputDTO) -> ReminderDTO:
        """Raises:
        ReminderNotFoundError: no live reminder with this id is theirs.
        """
        reminder = await self._get_owned_reminder(dto=dto)
        now = self.now_provider()
        firing = await self.reminder_repository.get_latest_firing(
            user_id=dto.user_id, reminder_id=dto.reminder_id
        )
        updated = await self.reminder_repository.record_action(
            user_id=dto.user_id,
            reminder_id=dto.reminder_id,
            firing_id=firing.id if firing is not None else None,
            action="done",
            acted_at=now,
            state=self._state_after_done(reminder=reminder),
        )
        if updated is None:
            raise ReminderNotFoundError()
        if firing is not None:
            await self.notifications.record_action(
                user_id=dto.user_id, firing_id=firing.id, action="done", acted_at=now
            )
        return updated

    async def _get_owned_reminder(
        self, *, dto: MarkReminderDoneInputDTO
    ) -> ReminderDTO:
        reminder = await self.reminder_repository.get_by_id(
            user_id=dto.user_id, reminder_id=dto.reminder_id
        )
        if reminder is None:
            raise ReminderNotFoundError()
        return reminder

    def _state_after_done(self, *, reminder: ReminderDTO) -> ReminderStateWrite:
        is_one_time = reminder.spec.repeat_kind is RepeatKind.NONE
        return ReminderStateWrite(
            state="done" if is_one_time else "upcoming",
            next_fire_at=None if is_one_time else reminder.next_fire_at,
            snoozed_until=None,
            last_fired_at=reminder.last_fired_at,
            last_action="done",
        )
