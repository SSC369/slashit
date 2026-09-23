"""FR-37: mark every notification read at once."""

from collections.abc import Callable
from datetime import datetime
from uuid import UUID

from app.domains.notifications.interfaces.repositories import NotificationRepository


class MarkAllReadInteractor:
    def __init__(
        self,
        *,
        notification_repository: NotificationRepository,
        now_provider: Callable[[], datetime],
    ) -> None:
        self.notification_repository = notification_repository
        self.now_provider = now_provider

    async def mark_all_read(self, *, user_id: UUID) -> int:
        """Returns how many were unread."""
        return await self.notification_repository.mark_all_read(
            user_id=user_id, now=self.now_provider()
        )
