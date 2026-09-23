"""The published entry point other domains call to tell a user something."""

from collections.abc import Callable
from datetime import datetime, time
from uuid import UUID
from zoneinfo import ZoneInfo

import structlog

from app.domains.notifications.constants import (
    EMAIL_PAUSED_DETAIL,
    EMAIL_PAUSED_TITLE,
    MAX_EMAILS_PER_DAY,
)
from app.domains.notifications.interfaces.dtos import (
    DeliverySettings,
    DeliveryStatusValue,
    NotificationActionValue,
    NotificationDTO,
    PublishNotification,
)
from app.domains.notifications.interfaces.ports import (
    DeliverySettingsPort,
    EmailQueuePort,
)
from app.domains.notifications.interfaces.repositories import NotificationRepository

logger = structlog.get_logger(__name__)


class NotificationService:
    def __init__(
        self,
        *,
        notification_repository: NotificationRepository,
        delivery_settings: DeliverySettingsPort,
        email_queue: EmailQueuePort,
        is_email_configured: bool,
        now_provider: Callable[[], datetime],
    ) -> None:
        self.notification_repository = notification_repository
        self.delivery_settings = delivery_settings
        self.email_queue = email_queue
        # The kill switch (index §9): off, no email is ever queued.
        self.is_email_configured = is_email_configured
        self.now_provider = now_provider

    async def publish(self, *, publish: PublishNotification) -> NotificationDTO | None:
        """Write the list row (FR-12, always), decide the pop-up (FR-13) and the
        email (FR-14, FR-18, FR-39), then queue the email. Safe to call twice
        for one source: the second call writes nothing, returns None, and
        re-queues an email still waiting, in case the first call stopped
        between the commit and the queue (AD-3)."""
        now = self.now_provider()
        settings = await self.delivery_settings.get_delivery_settings(
            user_id=publish.user_id
        )
        email_status = await self._decide_email(
            publish=publish, settings=settings, now=now
        )
        published = await self.notification_repository.insert_notification(
            publish=publish,
            show_popup=settings.popups_enabled,
            email_status=email_status,
            now=now,
        )
        if published is None:
            await self._requeue_waiting_email(publish=publish)
            return None
        if published.email_status == "queued":
            await self.email_queue.enqueue_email(
                delivery_id=published.email_delivery_id
            )
        return published.notification

    async def record_action(
        self,
        *,
        user_id: UUID,
        source_id: UUID,
        action: NotificationActionValue,
        acted_at: datetime,
    ) -> None:
        """What the user did about a firing, so the panel can say "marked done
        9:41 AM" and stop offering Done."""
        await self.notification_repository.record_action(
            user_id=user_id, source_id=source_id, action=action, acted_at=acted_at
        )

    async def _decide_email(
        self, *, publish: PublishNotification, settings: DeliverySettings, now: datetime
    ) -> DeliveryStatusValue:
        if publish.kind == "reminder" and not self.is_email_configured:
            # 4.3 §8: until a sending domain is set, every firing says why
            # it sent no email.
            logger.info(
                "notifications.email_disabled", source_id=str(publish.source_id)
            )
        is_wanted = (
            publish.kind == "reminder"
            and self.is_email_configured
            and settings.email_enabled
            and publish.marker != "missed"
        )
        if not is_wanted:
            return "skipped"
        if await self._is_over_daily_cap(publish=publish, settings=settings, now=now):
            return "skipped"
        return "queued"

    async def _is_over_daily_cap(
        self, *, publish: PublishNotification, settings: DeliverySettings, now: datetime
    ) -> bool:
        """FR-39, counted in the user's own day. The first firing past the cap
        leaves one notice in the list; later ones that day leave none."""
        day_start = _start_of_local_day(now=now, timezone=settings.timezone)
        sent_today = await self.notification_repository.count_emails_since(
            user_id=publish.user_id, since=day_start
        )
        if sent_today < MAX_EMAILS_PER_DAY:
            return False
        already_noticed = await self.notification_repository.has_email_paused_since(
            user_id=publish.user_id, since=day_start
        )
        if not already_noticed:
            await self.notification_repository.insert_notification(
                publish=PublishNotification(
                    user_id=publish.user_id,
                    kind="email_paused",
                    source_id=None,
                    target_id=None,
                    title=EMAIL_PAUSED_TITLE,
                    detail=EMAIL_PAUSED_DETAIL,
                    marker="on_time",
                    occurred_at=now,
                    time_zone=settings.timezone,
                ),
                show_popup=False,
                email_status="skipped",
                now=now,
            )
            logger.info("notifications.email_paused", user_id=str(publish.user_id))
        return True

    async def _requeue_waiting_email(self, *, publish: PublishNotification) -> None:
        if publish.source_id is None:
            return
        email = await self.notification_repository.get_email_status_for_source(
            user_id=publish.user_id, source_id=publish.source_id
        )
        if email is not None and email[1] == "queued":
            await self.email_queue.enqueue_email(delivery_id=email[0])


def _start_of_local_day(*, now: datetime, timezone: str) -> datetime:
    zone = ZoneInfo(timezone)
    return datetime.combine(now.astimezone(zone).date(), time(0), tzinfo=zone)
