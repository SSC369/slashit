"""The published entry point other domains call to tell a user something."""

from collections.abc import Callable
from datetime import datetime
from uuid import UUID

from app.domains.notifications.interfaces.dtos import (
    NotificationActionValue,
    NotificationDTO,
    PublishNotification,
)
from app.domains.notifications.interfaces.ports import DeliverySettingsPort
from app.domains.notifications.interfaces.repositories import NotificationRepository


class NotificationService:
    def __init__(
        self,
        *,
        notification_repository: NotificationRepository,
        delivery_settings: DeliverySettingsPort,
        now_provider: Callable[[], datetime],
    ) -> None:
        self.notification_repository = notification_repository
        self.delivery_settings = delivery_settings
        self.now_provider = now_provider

    async def publish(self, *, publish: PublishNotification) -> NotificationDTO | None:
        """Write the list row (FR-12) and decide the pop-up (FR-13). Safe to
        call twice for one source: the second call writes nothing and returns
        None (AD-3)."""
        show_popup = await self.delivery_settings.popups_enabled(
            user_id=publish.user_id
        )
        return await self.notification_repository.insert_notification(
            publish=publish, show_popup=show_popup, now=self.now_provider()
        )

    async def record_action(
        self,
        *,
        user_id: UUID,
        source_id: UUID,
        action: NotificationActionValue,
        acted_at: datetime,
    ) -> None:
        """What the user did about a firing, so the panel can say "marked done
        9:41 AM" and stop offering Done."""
        await self.notification_repository.record_action(
            user_id=user_id, source_id=source_id, action=action, acted_at=acted_at
        )
