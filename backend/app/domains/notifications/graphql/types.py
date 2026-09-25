"""Notifications' own GraphQL types. ``Notification`` is in interfaces/dtos.py."""

import strawberry

from app.domains.notifications.interfaces.dtos import (
    Notification,
    NotificationPageDTO,
    notification_dto_to_type,
)


@strawberry.type
class NotificationPage:
    items: list[Notification]
    next_cursor: str | None


@strawberry.type
class MarkAllNotificationsReadSucceeded:
    marked_count: int


def notification_page_to_type(*, page: NotificationPageDTO) -> NotificationPage:
    return NotificationPage(
        items=[notification_dto_to_type(notification=item) for item in page.items],
        next_cursor=page.next_cursor,
    )
