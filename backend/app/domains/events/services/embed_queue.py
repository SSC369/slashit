"""Queues the event embed job on Procrastinate. The only place events names
it."""

from uuid import UUID

import structlog
from procrastinate.exceptions import AlreadyEnqueued, AppNotOpen, ConnectorException

from app.core.jobs import procrastinate_app

EMBED_EVENT_JOB = "events.embed_event"

logger = structlog.get_logger(__name__)


class ProcrastinateEventEmbedQueue:
    async def queue_event_embed(
        self, *, user_id: UUID, event_id: UUID, delay_seconds: int
    ) -> None:
        """Deferred by name, so this module never imports the job back. The
        queueing lock collapses two quick edits into one pending embed. The
        event is already committed, so a queue that cannot be reached never
        fails the save; the periodic backfill queues it later (004 P-6)."""
        try:
            await procrastinate_app.configure_task(
                name=EMBED_EVENT_JOB,
                queueing_lock=f"embed-event:{event_id}",
                schedule_in={"seconds": delay_seconds},
            ).defer_async(user_id=str(user_id), event_id=str(event_id))
        except AlreadyEnqueued:
            return
        except (ConnectorException, AppNotOpen):
            logger.warning("events.embed_event_enqueue_failed", event_id=str(event_id))
