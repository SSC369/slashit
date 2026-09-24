"""NFR-4: find reminders that are overdue and never fired, and say so loudly.

``fire_one`` moves ``next_fire_at`` forward on every firing, missed ones
included. A reminder still overdue past the late threshold has therefore had
neither a firing nor a missed marker. This job only reports it (4.4 decision
2): the every-minute sweep fires it once the worker is healthy again.
"""

from collections.abc import Callable
from datetime import datetime

import structlog

from app.domains.reminders.constants import LOST_AFTER, RECONCILE_BATCH
from app.domains.reminders.interfaces.repositories import ReminderRepository

logger = structlog.get_logger(__name__)


class ReconcileRemindersInteractor:
    def __init__(
        self,
        *,
        reminder_repository: ReminderRepository,
        now_provider: Callable[[], datetime],
    ) -> None:
        self.reminder_repository = reminder_repository
        self.now_provider = now_provider

    async def reconcile(self) -> int:
        """Returns how many reminders are lost; logs one error for each."""
        now = self.now_provider()
        lost = await self.reminder_repository.select_due(
            now=now - LOST_AFTER, limit=RECONCILE_BATCH
        )
        for due in lost:
            # Ids and times only: never reminder text in logs (T6).
            logger.error(
                "reminders.lost",
                reminder_id=str(due.reminder_id),
                due_at=due.due_at.isoformat(),
                minutes_overdue=int((now - due.due_at).total_seconds() // 60),
            )
        return len(lost)
