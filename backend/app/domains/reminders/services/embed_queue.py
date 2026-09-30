"""Queues the reminder embed job on Procrastinate. The only place reminders
names it."""

from uuid import UUID

import structlog
from procrastinate.exceptions import AlreadyEnqueued, AppNotOpen, ConnectorException

from app.core.jobs import procrastinate_app

EMBED_REMINDER_JOB = "reminders.embed_reminder"

logger = structlog.get_logger(__name__)


class ProcrastinateReminderEmbedQueue:
    async def queue_reminder_embed(
        self, *, user_id: UUID, reminder_id: UUID, delay_seconds: int
    ) -> None:
        """Deferred by name, so this module never imports the job back. The
        queueing lock collapses two quick edits into one pending embed.

        The reminder is already committed when this runs, so a queue that
        cannot be reached must not fail the save (004 P-6). The periodic
        backfill queues it later."""
        try:
            await procrastinate_app.configure_task(
                name=EMBED_REMINDER_JOB,
                queueing_lock=f"embed-reminder:{reminder_id}",
                schedule_in={"seconds": delay_seconds},
            ).defer_async(user_id=str(user_id), reminder_id=str(reminder_id))
        except AlreadyEnqueued:
            return
        # AppNotOpen: a process that never opened the queue, such as a test
        # of an unrelated feature. The save stands either way; the periodic
        # backfill queues the vector within ten minutes.
        except (ConnectorException, AppNotOpen):
            logger.warning(
                "reminders.embed_reminder_enqueue_failed", reminder_id=str(reminder_id)
            )
