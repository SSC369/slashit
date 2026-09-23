"""FR-37: opening a notification marks it read."""

from collections.abc import Callable
from datetime import datetime

from app.domains.notifications.graphql.errors import NotificationNotFoundError
from app.domains.notifications.interactors.dtos import MarkNotificationReadInputDTO
from app.domains.notifications.interfaces.dtos import NotificationDTO
from app.domains.notifications.interfaces.repositories import NotificationRepository


class MarkNotificationReadInteractor:
    def __init__(
        self,
        *,
        notification_repository: NotificationRepository,
        now_provider: Callable[[], datetime],
    ) -> None:
        self.notification_repository = notification_repository
        self.now_provider = now_provider

    async def mark_notification_read(
        self, *, dto: MarkNotificationReadInputDTO
    ) -> NotificationDTO:
        """Marks it read, once; a second call leaves the first time in place.

        Raises:
            NotificationNotFoundError: no notification with this id is theirs.
        """
        notification = await self.notification_repository.mark_read(
            user_id=dto.user_id,
            notification_id=dto.notification_id,
            now=self.now_provider(),
        )
        if notification is None:
            raise NotificationNotFoundError()
        return notification
