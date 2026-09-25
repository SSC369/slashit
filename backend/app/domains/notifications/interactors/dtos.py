"""Input DTOs, one per use case."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ListNotificationsInputDTO:
    user_id: UUID
    cursor: str | None


@dataclass(frozen=True)
class MarkNotificationReadInputDTO:
    user_id: UUID
    notification_id: UUID
