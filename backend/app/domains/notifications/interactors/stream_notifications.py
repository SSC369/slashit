"""FR-13: each notification written for the user, as it is written."""

from collections.abc import AsyncIterator
from uuid import UUID

from app.domains.notifications.interfaces.dtos import NotificationDTO
from app.domains.notifications.interfaces.ports import NotificationSignalPort
from app.domains.notifications.interfaces.repositories import NotificationRepository


class StreamNotificationsInteractor:
    def __init__(
        self,
        *,
        notification_repository: NotificationRepository,
        signal: NotificationSignalPort,
    ) -> None:
        self.notification_repository = notification_repository
        self.signal = signal

    async def stream_notifications(
        self, *, user_id: UUID
    ) -> AsyncIterator[NotificationDTO]:
        """Reads each signalled id back as this user, so Row Level Security,
        not the signal, decides what reaches them (NFR-6)."""
        async with self.signal.subscribe(user_id=user_id) as subscription:
            while True:
                notification_id = await subscription.next_notification_id()
                notification = await self.notification_repository.get(
                    user_id=user_id, notification_id=notification_id
                )
                if notification is not None:
                    yield notification
