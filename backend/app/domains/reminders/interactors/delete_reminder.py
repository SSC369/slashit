"""FR-29, FR-30: delete a reminder, the whole series if it repeats."""

from app.domains.reminders.graphql.errors import ReminderNotFoundError
from app.domains.reminders.interactors.dtos import DeleteReminderInputDTO
from app.domains.reminders.interfaces.ports import NotificationPort
from app.domains.reminders.interfaces.repositories import ReminderRepository


class DeleteReminderInteractor:
    def __init__(
        self,
        *,
        reminder_repository: ReminderRepository,
        notifications: NotificationPort,
    ) -> None:
        self.reminder_repository = reminder_repository
        self.notifications = notifications

    async def delete_reminder(self, *, dto: DeleteReminderInputDTO) -> None:
        """Soft-delete it. Clearing ``next_fire_at`` in the same write is what
        keeps a deleted reminder from ever firing (FR-30). Its notification
        history stops showing too, so an old "Open" never lands on a page
        that says the reminder is gone.

        Raises:
            ReminderNotFoundError: no live reminder with this id is theirs.
        """
        was_deleted = await self.reminder_repository.soft_delete(
            user_id=dto.user_id, reminder_id=dto.reminder_id
        )
        if not was_deleted:
            raise ReminderNotFoundError()
        await self.notifications.hide_for_reminder(
            user_id=dto.user_id, reminder_id=dto.reminder_id
        )
