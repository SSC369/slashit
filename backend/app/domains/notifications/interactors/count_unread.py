"""FR-36: the bell's count."""

from uuid import UUID

from app.domains.notifications.interfaces.repositories import NotificationRepository


class CountUnreadInteractor:
    def __init__(self, *, notification_repository: NotificationRepository) -> None:
        self.notification_repository = notification_repository

    async def count_unread(self, *, user_id: UUID) -> int:
        return await self.notification_repository.count_unread(user_id=user_id)
