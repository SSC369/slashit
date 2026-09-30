"""Queues the task embed job on Procrastinate. The only place records names it."""

from uuid import UUID

import structlog
from procrastinate.exceptions import AlreadyEnqueued, AppNotOpen, ConnectorException

from app.core.jobs import procrastinate_app

EMBED_TASK_JOB = "records.embed_task"

logger = structlog.get_logger(__name__)


class ProcrastinateTaskEmbedQueue:
    async def queue_task_embed(
        self, *, user_id: UUID, task_id: UUID, delay_seconds: int
    ) -> None:
        """Deferred by name, so this module never imports the job back. The
        queueing lock collapses two quick edits into one pending embed.

        The task is already committed when this runs, so a queue that cannot
        be reached must not fail the save (004 P-6). The periodic backfill
        queues it later."""
        try:
            await procrastinate_app.configure_task(
                name=EMBED_TASK_JOB,
                queueing_lock=f"embed-task:{task_id}",
                schedule_in={"seconds": delay_seconds},
            ).defer_async(user_id=str(user_id), task_id=str(task_id))
        except AlreadyEnqueued:
            return
        # AppNotOpen: a process that never opened the queue, such as a test
        # of an unrelated feature. The save stands either way; the periodic
        # backfill queues the vector within ten minutes.
        except (ConnectorException, AppNotOpen):
            logger.warning("records.embed_task_enqueue_failed", task_id=str(task_id))
