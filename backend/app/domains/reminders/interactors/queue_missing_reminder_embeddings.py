"""Queue a vector for reminders that have none. Run by the
`reminders.backfill_embeddings` job (005 AD-7, following 004 P-6)."""

from collections.abc import Callable
from datetime import datetime, timedelta
from uuid import UUID

from app.domains.reminders.constants import (
    BACKFILL_CALLS_PER_SECOND,
    EMBEDDING_BACKFILL_BATCH,
    EMBEDDING_BACKFILL_WINDOW_HOURS,
)
from app.domains.reminders.interactors.dtos import (
    QueueMissingReminderEmbeddingsInputDTO,
)
from app.domains.reminders.interfaces.dtos import ReminderEmbeddingTargetDTO
from app.domains.reminders.interfaces.ports import ReminderEmbedQueue
from app.domains.reminders.interfaces.repositories import ReminderRepository


class QueueMissingReminderEmbeddingsInteractor:
    def __init__(
        self,
        *,
        reminder_repository: ReminderRepository,
        embed_queue: ReminderEmbedQueue,
        now_provider: Callable[[], datetime],
    ) -> None:
        self.reminder_repository = reminder_repository
        self.embed_queue = embed_queue
        self.now_provider = now_provider

    async def queue_missing_reminder_embeddings(
        self, *, dto: QueueMissingReminderEmbeddingsInputDTO
    ) -> int:
        """Returns how many reminders were handed to the queue.

        The periodic sweep queues one batch of recently touched reminders. The
        full sweep, run once at deploy (FR-13), walks every reminder with no
        vector and spaces the jobs out (index §6). The queue's lock keeps a
        reminder already waiting from being queued twice."""
        if dto.full:
            return await self._queue_every_missing_reminder()
        recent = await self.reminder_repository.select_missing_embeddings(
            updated_since=self.now_provider()
            - timedelta(hours=EMBEDDING_BACKFILL_WINDOW_HOURS),
            after_id=None,
            limit=EMBEDDING_BACKFILL_BATCH,
        )
        return await self._queue_targets(targets=recent, first_position=0)

    async def _queue_every_missing_reminder(self) -> int:
        queued_count = 0
        after_id: UUID | None = None
        while True:
            page = await self.reminder_repository.select_missing_embeddings(
                updated_since=None, after_id=after_id, limit=EMBEDDING_BACKFILL_BATCH
            )
            if not page:
                return queued_count
            queued_count += await self._queue_targets(
                targets=page, first_position=queued_count
            )
            after_id = page[-1].reminder_id

    async def _queue_targets(
        self, *, targets: list[ReminderEmbeddingTargetDTO], first_position: int
    ) -> int:
        for offset, target in enumerate(targets):
            await self.embed_queue.queue_reminder_embed(
                user_id=target.user_id,
                reminder_id=target.reminder_id,
                delay_seconds=(first_position + offset) // BACKFILL_CALLS_PER_SECOND,
            )
        return len(targets)
