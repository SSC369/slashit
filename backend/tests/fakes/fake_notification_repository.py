"""An in-memory NotificationRepository. Not a mock: it behaves."""

import uuid
from dataclasses import replace
from datetime import datetime

from app.domains.notifications.interfaces.dtos import (
    NotificationActionValue,
    NotificationDTO,
    NotificationPageDTO,
    PublishNotification,
)


class FakeNotificationRepository:
    def __init__(self) -> None:
        self.rows: dict[uuid.UUID, NotificationDTO] = {}

    async def insert_notification(
        self, *, publish: PublishNotification, show_popup: bool, now: datetime
    ) -> NotificationDTO | None:
        if any(row.source_id == publish.source_id for row in self.rows.values()):
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
            created_at=now,
            read_at=None,
            action=None,
            acted_at=None,
            show_popup=show_popup,
        )
        self.rows[notification.id] = notification
        return notification

    async def list_page(
        self, *, user_id: uuid.UUID, cursor: str | None, limit: int
    ) -> NotificationPageDTO:
        items = sorted(
            (row for row in self.rows.values() if row.user_id == user_id),
            key=lambda row: row.created_at,
            reverse=True,
        )
        return NotificationPageDTO(items=items[:limit], next_cursor=None)

    async def count_unread(self, *, user_id: uuid.UUID) -> int:
        return sum(
            1
            for row in self.rows.values()
            if row.user_id == user_id and row.read_at is None
        )

    async def get(
        self, *, user_id: uuid.UUID, notification_id: uuid.UUID
    ) -> NotificationDTO | None:
        row = self.rows.get(notification_id)
        return row if row is not None and row.user_id == user_id else None

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
            row
            for row in self.rows.values()
            if row.user_id == user_id and row.read_at is None
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
        for row in list(self.rows.values()):
            if row.user_id == user_id and row.source_id == source_id:
                self.rows[row.id] = replace(
                    row,
                    action=action,
                    acted_at=acted_at,
                    read_at=row.read_at or acted_at,
                )
