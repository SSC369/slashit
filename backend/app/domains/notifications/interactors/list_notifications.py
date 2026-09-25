"""FR-35: the user's notifications, newest first, a page at a time."""

from app.domains.notifications.constants import NOTIFICATION_PAGE_SIZE
from app.domains.notifications.interactors.dtos import ListNotificationsInputDTO
from app.domains.notifications.interfaces.dtos import NotificationPageDTO
from app.domains.notifications.interfaces.repositories import NotificationRepository


class ListNotificationsInteractor:
    def __init__(self, *, notification_repository: NotificationRepository) -> None:
        self.notification_repository = notification_repository

    async def list_notifications(
        self, *, dto: ListNotificationsInputDTO
    ) -> NotificationPageDTO:
        return await self.notification_repository.list_page(
            user_id=dto.user_id, cursor=dto.cursor, limit=NOTIFICATION_PAGE_SIZE
        )
