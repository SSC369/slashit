"""FR-14, FR-15: send one reminder email. Run by the `send_email` job."""

from collections.abc import Callable
from datetime import datetime
from typing import Literal
from uuid import UUID

import structlog

from app.domains.notifications.constants import SEND_EMAIL_MAX_ATTEMPTS
from app.domains.notifications.interfaces.dtos import EmailDeliveryDTO
from app.domains.notifications.interfaces.ports import (
    EmailSenderPort,
    EmailSendError,
    RecipientPort,
)
from app.domains.notifications.interfaces.repositories import NotificationRepository
from app.domains.notifications.services.email_content import compose_reminder_email

logger = structlog.get_logger(__name__)

SendOutcomeValue = Literal["sent", "skipped", "failed"]


class SendEmailInteractor:
    def __init__(
        self,
        *,
        notification_repository: NotificationRepository,
        recipient: RecipientPort,
        sender: EmailSenderPort,
        app_base_url: str,
        now_provider: Callable[[], datetime],
    ) -> None:
        self.notification_repository = notification_repository
        self.recipient = recipient
        self.sender = sender
        self.app_base_url = app_base_url
        self.now_provider = now_provider

    async def send_email(self, *, delivery_id: UUID) -> SendOutcomeValue:
        """Sends a queued delivery once. A provider failure raises, so the job
        retries; the fifth failure marks the delivery failed instead. The list
        row already landed and is never touched (FR-33).

        Raises:
            EmailSendError: the provider refused, and attempts remain.
        """
        delivery = await self.notification_repository.get_email_delivery(
            delivery_id=delivery_id
        )
        if delivery is None or delivery.status != "queued":
            return "skipped"
        to = await self.recipient.email_address(user_id=delivery.user_id)
        if to is None:
            await self._give_up(delivery=delivery, reason="no_address")
            return "failed"
        now = self.now_provider()
        content = compose_reminder_email(
            delivery=delivery, app_base_url=self.app_base_url, now=now
        )
        try:
            message_id = await self.sender.send(
                idempotency_key=str(delivery.delivery_id),
                to=to,
                subject=content.subject,
                html=content.html,
                text=content.text,
            )
        except EmailSendError:
            is_final = delivery.attempts + 1 >= SEND_EMAIL_MAX_ATTEMPTS
            await self._record_failure(delivery=delivery, is_final=is_final)
            if is_final:
                return "failed"
            raise
        await self.notification_repository.mark_email_sent(
            user_id=delivery.user_id,
            delivery_id=delivery.delivery_id,
            provider_message_id=message_id,
            sent_at=now,
        )
        self._log_sent(delivery=delivery, sent_at=now)
        return "sent"

    async def _record_failure(
        self, *, delivery: EmailDeliveryDTO, is_final: bool
    ) -> None:
        attempts = await self.notification_repository.record_email_failure(
            user_id=delivery.user_id,
            delivery_id=delivery.delivery_id,
            is_final=is_final,
        )
        logger.warning(
            "notifications.email_failed" if is_final else "notifications.email_retry",
            delivery_id=str(delivery.delivery_id),
            attempts=attempts,
        )

    async def _give_up(self, *, delivery: EmailDeliveryDTO, reason: str) -> None:
        await self.notification_repository.record_email_failure(
            user_id=delivery.user_id, delivery_id=delivery.delivery_id, is_final=True
        )
        logger.warning(
            "notifications.email_failed",
            delivery_id=str(delivery.delivery_id),
            reason=reason,
        )

    def _log_sent(self, *, delivery: EmailDeliveryDTO, sent_at: datetime) -> None:
        """NFR-2 is read from ``handoff_ms``: firing to accepted by the provider."""
        handoff_ms = int(
            (sent_at - delivery.notification_created_at).total_seconds() * 1000
        )
        logger.info(
            "notifications.email_sent",
            delivery_id=str(delivery.delivery_id),
            handoff_ms=handoff_ms,
        )
