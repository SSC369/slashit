"""Queue a vector for events that have none. Run by the
`events.backfill_embeddings` job (005 AD-7, as reminders and expenses)."""

from collections.abc import Callable
from datetime import datetime, timedelta
from uuid import UUID

from app.domains.events.constants import (
    BACKFILL_CALLS_PER_SECOND,
    EMBEDDING_BACKFILL_BATCH,
    EMBEDDING_BACKFILL_WINDOW_HOURS,
)
from app.domains.events.interactors.dtos import QueueMissingEventEmbeddingsInputDTO
from app.domains.events.interfaces.dtos import EventTargetDTO
from app.domains.events.interfaces.ports import EventEmbedQueue
from app.domains.events.interfaces.repositories import EventRepository


class QueueMissingEventEmbeddingsInteractor:
    def __init__(
        self,
        *,
        event_repository: EventRepository,
        embed_queue: EventEmbedQueue,
        now_provider: Callable[[], datetime],
    ) -> None:
        self.event_repository = event_repository
        self.embed_queue = embed_queue
        self.now_provider = now_provider

    async def queue_missing_event_embeddings(
        self, *, dto: QueueMissingEventEmbeddingsInputDTO
    ) -> int:
        """Returns how many events were handed to the queue. The periodic sweep
        queues one batch of recently touched events; the full sweep, run once
        at deploy (4.2 T-2.16), walks every event with no vector and spaces
        the jobs out. The queue's lock keeps one already waiting from being
        queued twice."""
        if dto.full:
            return await self._queue_every_missing_event()
        recent = await self.event_repository.select_missing_embeddings(
            updated_since=self.now_provider()
            - timedelta(hours=EMBEDDING_BACKFILL_WINDOW_HOURS),
            after_id=None,
            limit=EMBEDDING_BACKFILL_BATCH,
        )
        return await self._queue_targets(targets=recent, first_position=0)

    async def _queue_every_missing_event(self) -> int:
        queued_count = 0
        after_id: UUID | None = None
        while True:
            page = await self.event_repository.select_missing_embeddings(
                updated_since=None, after_id=after_id, limit=EMBEDDING_BACKFILL_BATCH
            )
            if not page:
                return queued_count
            queued_count += await self._queue_targets(
                targets=page, first_position=queued_count
            )
            after_id = page[-1].event_id

    async def _queue_targets(
        self, *, targets: list[EventTargetDTO], first_position: int
    ) -> int:
        for offset, target in enumerate(targets):
            await self.embed_queue.queue_event_embed(
                user_id=target.user_id,
                event_id=target.event_id,
                delay_seconds=(first_position + offset) // BACKFILL_CALLS_PER_SECOND,
            )
        return len(targets)
