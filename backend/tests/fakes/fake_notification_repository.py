"""An in-memory NotificationRepository. Not a mock: it behaves."""

import uuid
from dataclasses import dataclass, replace
from datetime import datetime

from app.domains.notifications.interfaces.dtos import (
    DeliveryStatusValue,
    EmailDeliveryDTO,
    NotificationActionValue,
    NotificationDTO,
    NotificationPageDTO,
    PublishedNotification,
    PublishNotification,
)


@dataclass
class FakeEmailDelivery:
    id: uuid.UUID
    notification_id: uuid.UUID
    status: DeliveryStatusValue
    attempts: int = 0
    provider_message_id: str | None = None
    sent_at: datetime | None = None


class FakeNotificationRepository:
    def __init__(self) -> None:
        self.rows: dict[uuid.UUID, NotificationDTO] = {}
        self.emails: dict[uuid.UUID, FakeEmailDelivery] = {}
        # Ids stamped by the 90-day purge; the reads below skip them.
        self.deleted_ids: set[uuid.UUID] = set()

    def _live_rows_for(self, *, user_id: uuid.UUID) -> list[NotificationDTO]:
        return [
            row
            for row in self.rows.values()
            if row.user_id == user_id and row.id not in self.deleted_ids
        ]

    async def insert_notification(
        self,
        *,
        publish: PublishNotification,
        show_popup: bool,
        email_status: DeliveryStatusValue,
        now: datetime,
    ) -> PublishedNotification | None:
        is_repeat = publish.kind == "reminder" and any(
            row.kind == "reminder" and row.source_id == publish.source_id
            for row in self.rows.values()
        )
        if is_repeat:
            return None
        notification = NotificationDTO(
            id=uuid.uuid4(),
            user_id=publish.user_id,
            kind=publish.kind,
            source_id=publish.source_id,
            target_id=publish.target_id,
            title=publish.title,
            detail=publish.detail,
            marker=publish.marker,
            occurred_at=publish.occurred_at,
            time_zone=publish.time_zone,
            created_at=now,
            read_at=None,
            action=None,
            acted_at=None,
            show_popup=show_popup,
        )
        self.rows[notification.id] = notification
        delivery = FakeEmailDelivery(
            id=uuid.uuid4(), notification_id=notification.id, status=email_status
        )
        self.emails[delivery.id] = delivery
        return PublishedNotification(
            notification=notification,
            email_delivery_id=delivery.id,
            email_status=email_status,
        )

    async def get_email_status_for_source(
        self, *, user_id: uuid.UUID, source_id: uuid.UUID
    ) -> tuple[uuid.UUID, DeliveryStatusValue] | None:
        for delivery in self.emails.values():
            row = self.rows[delivery.notification_id]
            if row.user_id == user_id and row.source_id == source_id:
                return delivery.id, delivery.status
        return None

    async def count_emails_since(self, *, user_id: uuid.UUID, since: datetime) -> int:
        return sum(
            1
            for delivery in self.emails.values()
            if delivery.status in ("queued", "sent")
            and self.rows[delivery.notification_id].user_id == user_id
            and self.rows[delivery.notification_id].created_at >= since
        )

    async def has_email_paused_since(
        self, *, user_id: uuid.UUID, since: datetime
    ) -> bool:
        return any(
            row.user_id == user_id
            and row.kind == "email_paused"
            and row.created_at >= since
            for row in self.rows.values()
        )

    async def get_email_delivery(
        self, *, delivery_id: uuid.UUID
    ) -> EmailDeliveryDTO | None:
        delivery = self.emails.get(delivery_id)
        if delivery is None:
            return None
        row = self.rows[delivery.notification_id]
        return EmailDeliveryDTO(
            delivery_id=delivery.id,
            user_id=row.user_id,
            status=delivery.status,
            attempts=delivery.attempts,
            title=row.title,
            detail=row.detail,
            marker=row.marker,
            occurred_at=row.occurred_at,
            time_zone=row.time_zone,
            target_id=row.target_id,
            notification_created_at=row.created_at,
        )

    async def mark_email_sent(
        self,
        *,
        user_id: uuid.UUID,
        delivery_id: uuid.UUID,
        provider_message_id: str,
        sent_at: datetime,
    ) -> None:
        delivery = self.emails[delivery_id]
        delivery.status = "sent"
        delivery.provider_message_id = provider_message_id
        delivery.sent_at = sent_at
        delivery.attempts += 1

    async def record_email_failure(
        self, *, user_id: uuid.UUID, delivery_id: uuid.UUID, is_final: bool
    ) -> int:
        delivery = self.emails[delivery_id]
        delivery.attempts += 1
        if is_final:
            delivery.status = "failed"
        return delivery.attempts

    async def list_page(
        self, *, user_id: uuid.UUID, cursor: str | None, limit: int
    ) -> NotificationPageDTO:
        items = sorted(
            self._live_rows_for(user_id=user_id),
            key=lambda row: row.created_at,
            reverse=True,
        )
        return NotificationPageDTO(items=items[:limit], next_cursor=None)

    async def count_unread(self, *, user_id: uuid.UUID) -> int:
        return sum(
            1 for row in self._live_rows_for(user_id=user_id) if row.read_at is None
        )

    async def get(
        self, *, user_id: uuid.UUID, notification_id: uuid.UUID
    ) -> NotificationDTO | None:
        row = self.rows.get(notification_id)
        if row is None or row.user_id != user_id or row.id in self.deleted_ids:
            return None
        return row

    async def mark_read(
        self, *, user_id: uuid.UUID, notification_id: uuid.UUID, now: datetime
    ) -> NotificationDTO | None:
        row = await self.get(user_id=user_id, notification_id=notification_id)
        if row is None:
            return None
        if row.read_at is None:
            row = replace(row, read_at=now)
            self.rows[notification_id] = row
        return row

    async def mark_all_read(self, *, user_id: uuid.UUID, now: datetime) -> int:
        unread = [
            row for row in self._live_rows_for(user_id=user_id) if row.read_at is None
        ]
        for row in unread:
            self.rows[row.id] = replace(row, read_at=now)
        return len(unread)

    async def record_action(
        self,
        *,
        user_id: uuid.UUID,
        source_id: uuid.UUID,
        action: NotificationActionValue,
        acted_at: datetime,
    ) -> None:
        for row in self._live_rows_for(user_id=user_id):
            if row.source_id == source_id:
                self.rows[row.id] = replace(
                    row,
                    action=action,
                    acted_at=acted_at,
                    read_at=row.read_at or acted_at,
                )

    async def soft_delete_created_before(
        self, *, cutoff: datetime, now: datetime, limit: int
    ) -> int:
        old_ids = [
            row.id
            for row in self.rows.values()
            if row.id not in self.deleted_ids and row.created_at < cutoff
        ][:limit]
        self.deleted_ids.update(old_ids)
        return len(old_ids)
