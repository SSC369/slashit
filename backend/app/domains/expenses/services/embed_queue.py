"""Queues the expense embed job on Procrastinate. The only place expenses
names it."""

from uuid import UUID

import structlog
from procrastinate.exceptions import AlreadyEnqueued, AppNotOpen, ConnectorException

from app.core.jobs import procrastinate_app

EMBED_EXPENSE_JOB = "expenses.embed_expense"

logger = structlog.get_logger(__name__)


class ProcrastinateExpenseEmbedQueue:
    async def queue_expense_embed(
        self, *, user_id: UUID, expense_id: UUID, delay_seconds: int
    ) -> None:
        """Deferred by name, so this module never imports the job back. The
        queueing lock collapses two quick edits into one pending embed.

        The expense is already committed when this runs, so a queue that
        cannot be reached must not fail the save (004 P-6). The periodic
        backfill queues it later."""
        try:
            await procrastinate_app.configure_task(
                name=EMBED_EXPENSE_JOB,
                queueing_lock=f"embed-expense:{expense_id}",
                schedule_in={"seconds": delay_seconds},
            ).defer_async(user_id=str(user_id), expense_id=str(expense_id))
        except AlreadyEnqueued:
            return
        # AppNotOpen: a process that never opened the queue, such as a test
        # of an unrelated feature. The save stands either way; the periodic
        # backfill queues the vector within ten minutes.
        except (ConnectorException, AppNotOpen):
            logger.warning(
                "expenses.embed_expense_enqueue_failed", expense_id=str(expense_id)
            )
