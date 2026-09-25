"""The contract for notification storage. Storage reads and writes; it never decides."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domains.notifications.interfaces.dtos import (
    DeliveryStatusValue,
    EmailDeliveryDTO,
    NotificationActionValue,
    NotificationDTO,
    NotificationPageDTO,
    PublishedNotification,
    PublishNotification,
)


class NotificationRepository(Protocol):
    async def insert_notification(
        self,
        *,
        publish: PublishNotification,
        show_popup: bool,
        email_status: DeliveryStatusValue,
        now: datetime,
    ) -> PublishedNotification | None:
        """Insert the row, its pop-up and email deliveries, and signal open
        apps, in one transaction. None when a row for this ``source_id``
        already exists."""
        ...

    async def get_email_status_for_source(
        self, *, user_id: UUID, source_id: UUID
    ) -> tuple[UUID, DeliveryStatusValue] | None:
        """The email delivery of the notification published for a source."""
        ...

    async def count_emails_since(self, *, user_id: UUID, since: datetime) -> int:
        """Email deliveries queued or sent for notifications created since."""
        ...

    async def has_email_paused_since(
        self, *, user_id: UUID, since: datetime
    ) -> bool: ...

    async def get_email_delivery(self, *, delivery_id: UUID) -> EmailDeliveryDTO | None:
        """By id alone, for the email job on the service-role connection."""
        ...

    async def mark_email_sent(
        self,
        *,
        user_id: UUID,
        delivery_id: UUID,
        provider_message_id: str,
        sent_at: datetime,
    ) -> None: ...

    async def record_email_failure(
        self, *, user_id: UUID, delivery_id: UUID, is_final: bool
    ) -> int:
        """Counts one failed attempt, and marks the delivery failed when
        ``is_final``. Returns the attempts made so far."""
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

    async def soft_delete_created_before(
        self, *, cutoff: datetime, now: datetime, limit: int
    ) -> int:
        """Stamps ``deleted_at`` on up to ``limit`` live rows created before
        ``cutoff``, for every user. Service-role only (T3). Returns how many."""
        ...
