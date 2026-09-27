"""Queues the reembed job on Procrastinate. The only place memories names it."""

from uuid import UUID

import structlog
from procrastinate.exceptions import AlreadyEnqueued, ConnectorException

from app.core.jobs import procrastinate_app

REEMBED_TASK = "memories.reembed"

logger = structlog.get_logger(__name__)


class ProcrastinateReembedQueue:
    async def enqueue_reembed(self, *, user_id: UUID, memory_id: UUID) -> None:
        """Deferred by name, so this module never imports the task back. The
        queueing lock collapses two quick edits into one pending refresh.

        The memory is already committed when this runs, so a queue that cannot
        be reached must not fail the save (004 P-6: the answer reported "Nothing
        changed" and a retry saved it twice). The backfill job queues it later."""
        try:
            await procrastinate_app.configure_task(
                name=REEMBED_TASK, queueing_lock=f"reembed:{memory_id}"
            ).defer_async(user_id=str(user_id), memory_id=str(memory_id))
        except AlreadyEnqueued:
            return
        except ConnectorException:
            logger.warning("memories.reembed_enqueue_failed", memory_id=str(memory_id))
