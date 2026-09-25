"""FR-40: notifications older than 90 days leave the list, by soft delete."""

from collections.abc import Callable
from datetime import datetime, timedelta

from app.domains.notifications.constants import (
    NOTIFICATION_RETENTION_DAYS,
    PURGE_BATCH_SIZE,
)
from app.domains.notifications.interfaces.repositories import NotificationRepository


class PurgeOldNotificationsInteractor:
    def __init__(
        self,
        *,
        notification_repository: NotificationRepository,
        now_provider: Callable[[], datetime],
    ) -> None:
        self.notification_repository = notification_repository
        self.now_provider = now_provider

    async def purge_old_notifications(self) -> int:
        """Returns how many notifications left the list. Each batch commits on
        its own, so a run that fails part way loses nothing it already did."""
        now = self.now_provider()
        cutoff = now - timedelta(days=NOTIFICATION_RETENTION_DAYS)
        purged_count = 0
        while True:
            batch_count = await self.notification_repository.soft_delete_created_before(
                cutoff=cutoff, now=now, limit=PURGE_BATCH_SIZE
            )
            purged_count += batch_count
            if batch_count < PURGE_BATCH_SIZE:
                return purged_count
