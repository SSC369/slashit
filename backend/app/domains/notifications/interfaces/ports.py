"""What notifications needs from other domains and vendors, in its own words."""

from typing import Protocol
from uuid import UUID

from app.domains.notifications.interfaces.dtos import DeliverySettings


class DeliverySettingsPort(Protocol):
    """The user's pop-up and email switches (FR-13, FR-14), and their zone,
    which bounds the email cap's day (FR-39)."""

    async def get_delivery_settings(self, *, user_id: UUID) -> DeliverySettings: ...


class RecipientPort(Protocol):
    """Where a user's reminder email goes. None if the account is gone."""

    async def email_address(self, *, user_id: UUID) -> str | None: ...


class EmailSendError(Exception):
    """The provider did not accept the email. Safe to retry: the delivery id
    is the idempotency key, so a retry never sends twice (AD-3)."""


class EmailSenderPort(Protocol):
    async def send(
        self, *, idempotency_key: str, to: str, subject: str, html: str, text: str
    ) -> str:
        """Returns the provider's message id. Raises ``EmailSendError``."""
        ...


class EmailQueuePort(Protocol):
    async def enqueue_email(self, *, delivery_id: UUID) -> bool:
        """False when that delivery's job is already queued."""
        ...


class NotificationSignalPort(Protocol):
    """Open apps' live feed: the ids of notifications written for one user."""

    def subscribe(self, *, user_id: UUID) -> "NotificationSubscription": ...


class NotificationSubscription(Protocol):
    async def __aenter__(self) -> "NotificationSubscription": ...

    async def __aexit__(self, *exc_info: object) -> None: ...

    async def next_notification_id(self) -> UUID: ...
