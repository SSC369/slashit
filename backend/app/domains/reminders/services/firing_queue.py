"""Queues firing jobs on Procrastinate. The only place reminders names it."""

from datetime import datetime
from uuid import UUID

from procrastinate.exceptions import AlreadyEnqueued

from app.core.jobs import procrastinate_app

FIRE_ONE_TASK = "reminders.fire_one"


class ProcrastinateFiringQueue:
    async def enqueue_firing(
        self, *, reminder_id: UUID, scheduled_for: datetime
    ) -> bool:
        """Deferred by name, so this module never imports the task back. The
        queueing lock keeps a still-queued occurrence from being queued twice
        by the next minute's sweep (AD-2)."""
        scheduled_text = scheduled_for.isoformat()
        try:
            await procrastinate_app.configure_task(
                name=FIRE_ONE_TASK,
                queueing_lock=f"fire:{reminder_id}:{scheduled_text}",
            ).defer_async(reminder_id=str(reminder_id), scheduled_for=scheduled_text)
        except AlreadyEnqueued:
            return False
        return True
