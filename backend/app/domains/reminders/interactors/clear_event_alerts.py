"""Epic 007 FR-23: an event's alerts go with it."""

from app.domains.reminders.interactors.dtos import ClearEventAlertsInputDTO
from app.domains.reminders.interfaces.ports import NotificationPort
from app.domains.reminders.interfaces.repositories import ReminderRepository


class ClearEventAlertsInteractor:
    def __init__(
        self,
        *,
        reminder_repository: ReminderRepository,
        notifications: NotificationPort,
    ) -> None:
        self.reminder_repository = reminder_repository
        self.notifications = notifications

    async def clear_event_alerts(self, *, dto: ClearEventAlertsInputDTO) -> None:
        """Soft-delete every alert row of the event, which clears their fire
        times so none fires, and hide their notifications, as deleting a
        reminder does. Safe to repeat. Nothing raises.
        """
        await self.reminder_repository.soft_delete_event_alerts(
            user_id=dto.user_id, event_id=dto.event_id
        )
        await self.notifications.hide_for_event(
            user_id=dto.user_id, event_id=dto.event_id
        )
