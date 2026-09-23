"""In-memory stand-ins for notifications' email ports."""

from uuid import UUID

from app.domains.notifications.interfaces.dtos import DeliverySettings
from app.domains.notifications.interfaces.ports import EmailSendError


class FakeDeliverySettings:
    def __init__(
        self,
        *,
        popups_enabled: bool = True,
        email_enabled: bool = True,
        timezone: str = "Asia/Kolkata",
    ) -> None:
        self.settings = DeliverySettings(
            popups_enabled=popups_enabled,
            email_enabled=email_enabled,
            timezone=timezone,
        )

    async def get_delivery_settings(self, *, user_id: UUID) -> DeliverySettings:
        return self.settings


class FakeEmailQueue:
    def __init__(self) -> None:
        self.queued: list[UUID] = []

    async def enqueue_email(self, *, delivery_id: UUID) -> bool:
        if delivery_id in self.queued:
            return False
        self.queued.append(delivery_id)
        return True


class FakeRecipient:
    def __init__(self, *, address: str | None = "someone@example.test") -> None:
        self.address = address

    async def email_address(self, *, user_id: UUID) -> str | None:
        return self.address


class FakeEmailSender:
    """Records each send; fails the first ``failures`` calls."""

    def __init__(self, *, failures: int = 0) -> None:
        self.failures = failures
        self.sent: list[dict[str, str]] = []

    async def send(
        self, *, idempotency_key: str, to: str, subject: str, html: str, text: str
    ) -> str:
        if self.failures > 0:
            self.failures -= 1
            raise EmailSendError("provider refused")
        self.sent.append(
            {
                "idempotency_key": idempotency_key,
                "to": to,
                "subject": subject,
                "text": text,
            }
        )
        return f"message-{len(self.sent)}"
