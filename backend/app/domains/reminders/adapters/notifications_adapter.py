"""Implements reminders' NotificationPort against the notifications domain."""

from datetime import datetime
from uuid import UUID

from app.domains.notifications.public import NotificationService, PublishNotification
from app.domains.reminders.interfaces.dtos import FiringAnnouncement, UserActionValue


class NotificationsAdapter:
    def __init__(self, *, notification_service: NotificationService) -> None:
        self.notification_service = notification_service

    async def announce_firing(self, *, announcement: FiringAnnouncement) -> None:
        """An event alert opens its event and acts on its own row (epic 007
        AD-5, 4.2 Q2); a reminder opens and acts on itself."""
        is_event_alert = announcement.event_id is not None
        await self.notification_service.publish(
            publish=PublishNotification(
                user_id=announcement.user_id,
                kind="event_alert" if is_event_alert else "reminder",
                source_id=announcement.firing_id,
                target_id=announcement.event_id or announcement.reminder_id,
                action_target_id=announcement.reminder_id if is_event_alert else None,
                title=announcement.title,
                detail=announcement.detail,
                marker=announcement.lateness,
                occurred_at=announcement.occurred_at,
                time_zone=announcement.time_zone,
            )
        )

    async def record_action(
        self,
        *,
        user_id: UUID,
        firing_id: UUID,
        action: UserActionValue,
        acted_at: datetime,
    ) -> None:
        await self.notification_service.record_action(
            user_id=user_id, source_id=firing_id, action=action, acted_at=acted_at
        )

    async def hide_for_reminder(self, *, user_id: UUID, reminder_id: UUID) -> None:
        await self.notification_service.hide_for_target(
            user_id=user_id, target_id=reminder_id
        )

    async def hide_for_event(self, *, user_id: UUID, event_id: UUID) -> None:
        await self.notification_service.hide_for_target(
            user_id=user_id, target_id=event_id
        )
