"""The contract for notification storage. Storage reads and writes; it never decides."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domains.notifications.interfaces.dtos import (
    NotificationActionValue,
    NotificationDTO,
    NotificationPageDTO,
    PublishNotification,
)


class NotificationRepository(Protocol):
    async def insert_notification(
        self, *, publish: PublishNotification, show_popup: bool, now: datetime
    ) -> NotificationDTO | None:
        """Insert the row and its pop-up delivery, and signal open apps, in one
        transaction. None when a row for this ``source_id`` already exists."""
        ...

    async def list_page(
        self, *, user_id: UUID, cursor: str | None, limit: int
    ) -> NotificationPageDTO:
        """Newest first, by ``(created_at, id)``."""
        ...

    async def count_unread(self, *, user_id: UUID) -> int: ...

    async def get(
        self, *, user_id: UUID, notification_id: UUID
    ) -> NotificationDTO | None: ...

    async def mark_read(
        self, *, user_id: UUID, notification_id: UUID, now: datetime
    ) -> NotificationDTO | None:
        """Sets ``read_at`` if unset. None when not found."""
        ...

    async def mark_all_read(self, *, user_id: UUID, now: datetime) -> int: ...

    async def record_action(
        self,
        *,
        user_id: UUID,
        source_id: UUID,
        action: NotificationActionValue,
        acted_at: datetime,
    ) -> None:
        """Stamps what was done about the firing, and marks it read."""
        ...
