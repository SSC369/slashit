"""Data crossing the notifications domain's boundaries. Frozen, never a model.

``Notification``, the GraphQL shape, lives here beside its DTO so its
converter sits next to both, as reminders does.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID

import strawberry

NotificationKindValue = Literal["reminder", "email_paused"]
MarkerValue = Literal["on_time", "late", "missed"]
NotificationActionValue = Literal["done", "snoozed"]


@dataclass(frozen=True)
class PublishNotification:
    """What a caller hands to ``NotificationService.publish``.

    ``source_id`` is what makes a repeat a no-op (AD-3): one reminder
    notification per firing. ``target_id`` is what Open goes to (FR-22).
    """

    user_id: UUID
    kind: NotificationKindValue
    source_id: UUID
    target_id: UUID | None
    title: str
    detail: str
    marker: MarkerValue
    occurred_at: datetime


@dataclass(frozen=True)
class NotificationDTO:
    id: UUID
    user_id: UUID
    kind: NotificationKindValue
    source_id: UUID | None
    target_id: UUID | None
    title: str
    detail: str
    marker: MarkerValue
    occurred_at: datetime
    created_at: datetime
    read_at: datetime | None
    action: NotificationActionValue | None
    acted_at: datetime | None
    # The pop-up delivery's status at publish: the server decided, not the client.
    show_popup: bool


@dataclass(frozen=True)
class NotificationPageDTO:
    items: list[NotificationDTO]
    next_cursor: str | None


@strawberry.enum
class NotificationKind(Enum):
    REMINDER = "reminder"
    EMAIL_PAUSED = "email_paused"


@strawberry.enum
class NotificationMarker(Enum):
    """The panel's Late and Missed markers (FR-17, FR-18). NONE is on time."""

    NONE = "on_time"
    LATE = "late"
    MISSED = "missed"


@strawberry.enum
class NotificationAction(Enum):
    DONE = "done"
    SNOOZED = "snoozed"


@strawberry.type
class Notification:
    id: strawberry.ID
    kind: NotificationKind
    target_id: strawberry.ID | None
    title: str
    detail: str
    marker: NotificationMarker
    occurred_at: datetime
    created_at: datetime
    read: bool
    action: NotificationAction | None
    acted_at: datetime | None
    show_popup: bool


def notification_dto_to_type(*, notification: NotificationDTO) -> Notification:
    return Notification(
        id=strawberry.ID(str(notification.id)),
        kind=NotificationKind(notification.kind),
        target_id=(
            strawberry.ID(str(notification.target_id))
            if notification.target_id is not None
            else None
        ),
        title=notification.title,
        detail=notification.detail,
        marker=NotificationMarker(notification.marker),
        occurred_at=notification.occurred_at,
        created_at=notification.created_at,
        read=notification.read_at is not None,
        action=(
            NotificationAction(notification.action)
            if notification.action is not None
            else None
        ),
        acted_at=notification.acted_at,
        show_popup=notification.show_popup,
    )
