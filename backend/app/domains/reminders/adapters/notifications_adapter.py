"""Implements reminders' NotificationPort against the notifications domain."""

from datetime import datetime
from uuid import UUID

from app.domains.notifications.public import NotificationService, PublishNotification
from app.domains.reminders.interfaces.dtos import FiringAnnouncement, UserActionValue


class NotificationsAdapter:
    def __init__(self, *, notification_service: NotificationService) -> None:
        self.notification_service = notification_service

    async def announce_firing(self, *, announcement: FiringAnnouncement) -> None:
        await self.notification_service.publish(
            publish=PublishNotification(
                user_id=announcement.user_id,
                kind="reminder",
                source_id=announcement.firing_id,
                target_id=announcement.reminder_id,
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
