"""Queues the reembed job on Procrastinate. The only place memories names it."""

from uuid import UUID

from procrastinate.exceptions import AlreadyEnqueued

from app.core.jobs import procrastinate_app

REEMBED_TASK = "memories.reembed"


class ProcrastinateReembedQueue:
    async def enqueue_reembed(self, *, user_id: UUID, memory_id: UUID) -> None:
        """Deferred by name, so this module never imports the task back. The
        queueing lock collapses two quick edits into one pending refresh."""
        try:
            await procrastinate_app.configure_task(
                name=REEMBED_TASK, queueing_lock=f"reembed:{memory_id}"
            ).defer_async(user_id=str(user_id), memory_id=str(memory_id))
        except AlreadyEnqueued:
            return
