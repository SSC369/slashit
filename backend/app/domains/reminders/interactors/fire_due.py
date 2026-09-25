"""AD-2: every minute, queue one firing job per due occurrence. Fires nothing."""

from collections.abc import Callable
from datetime import datetime

import structlog

from app.domains.reminders.constants import FIRE_DUE_BATCH
from app.domains.reminders.interfaces.ports import FiringQueuePort
from app.domains.reminders.interfaces.repositories import ReminderRepository

logger = structlog.get_logger(__name__)


class FireDueInteractor:
    def __init__(
        self,
        *,
        reminder_repository: ReminderRepository,
        firing_queue: FiringQueuePort,
        now_provider: Callable[[], datetime],
        is_firing_enabled: bool = True,
    ) -> None:
        self.reminder_repository = reminder_repository
        self.firing_queue = firing_queue
        self.now_provider = now_provider
        # The index's kill switch, REMINDERS_FIRING_ENABLED (§9).
        self.is_firing_enabled = is_firing_enabled

    async def fire_due(self) -> int:
        """Returns how many firing jobs were newly queued. An occurrence whose
        job is still queued from the last sweep is not queued twice. With
        firing switched off, it queues nothing and reads nothing."""
        if not self.is_firing_enabled:
            logger.warning("reminders.firing_disabled")
            return 0
        due_reminders = await self.reminder_repository.select_due(
            now=self.now_provider(), limit=FIRE_DUE_BATCH
        )
        queued_count = 0
        for due in due_reminders:
            was_queued = await self.firing_queue.enqueue_firing(
                reminder_id=due.reminder_id, scheduled_for=due.due_at
            )
            queued_count += int(was_queued)
        return queued_count
