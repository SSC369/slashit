"""What notifications needs from other domains, in its own words."""

from typing import Protocol
from uuid import UUID


class DeliverySettingsPort(Protocol):
    """Whether the user wants a pop-up when a reminder fires (FR-13)."""

    async def popups_enabled(self, *, user_id: UUID) -> bool: ...


class NotificationSignalPort(Protocol):
    """Open apps' live feed: the ids of notifications written for one user."""

    def subscribe(self, *, user_id: UUID) -> "NotificationSubscription": ...


class NotificationSubscription(Protocol):
    async def __aenter__(self) -> "NotificationSubscription": ...

    async def __aexit__(self, *exc_info: object) -> None: ...

    async def next_notification_id(self) -> UUID: ...
