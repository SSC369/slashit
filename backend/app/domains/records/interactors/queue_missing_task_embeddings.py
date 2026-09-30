"""Queue a vector for tasks that have none. Run by the
`records.backfill_embeddings` job (005 AD-7, following 004 P-6)."""

from collections.abc import Callable
from datetime import datetime, timedelta
from uuid import UUID

from app.domains.records.constants import (
    BACKFILL_CALLS_PER_SECOND,
    EMBEDDING_BACKFILL_BATCH,
    EMBEDDING_BACKFILL_WINDOW_HOURS,
)
from app.domains.records.interactors.dtos import QueueMissingTaskEmbeddingsInputDTO
from app.domains.records.interfaces.dtos import TaskEmbeddingTargetDTO
from app.domains.records.interfaces.ports import TaskEmbedQueue
from app.domains.records.interfaces.repositories import TaskRepository


class QueueMissingTaskEmbeddingsInteractor:
    def __init__(
        self,
        *,
        task_repository: TaskRepository,
        embed_queue: TaskEmbedQueue,
        now_provider: Callable[[], datetime],
    ) -> None:
        self.task_repository = task_repository
        self.embed_queue = embed_queue
        self.now_provider = now_provider

    async def queue_missing_task_embeddings(
        self, *, dto: QueueMissingTaskEmbeddingsInputDTO
    ) -> int:
        """Returns how many tasks were handed to the queue.

        The periodic sweep queues one batch of recently touched tasks. The full
        sweep, run once at deploy (FR-13), walks every task with no vector and
        spaces the jobs out (index §6). The queue's lock keeps a task already
        waiting from being queued twice."""
        if dto.full:
            return await self._queue_every_missing_task()
        recent = await self.task_repository.select_missing_embeddings(
            updated_since=self.now_provider()
            - timedelta(hours=EMBEDDING_BACKFILL_WINDOW_HOURS),
            after_id=None,
            limit=EMBEDDING_BACKFILL_BATCH,
        )
        return await self._queue_targets(targets=recent, first_position=0)

    async def _queue_every_missing_task(self) -> int:
        queued_count = 0
        after_id: UUID | None = None
        while True:
            page = await self.task_repository.select_missing_embeddings(
                updated_since=None, after_id=after_id, limit=EMBEDDING_BACKFILL_BATCH
            )
            if not page:
                return queued_count
            queued_count += await self._queue_targets(
                targets=page, first_position=queued_count
            )
            after_id = page[-1].task_id

    async def _queue_targets(
        self, *, targets: list[TaskEmbeddingTargetDTO], first_position: int
    ) -> int:
        for offset, target in enumerate(targets):
            await self.embed_queue.queue_task_embed(
                user_id=target.user_id,
                task_id=target.task_id,
                delay_seconds=(first_position + offset) // BACKFILL_CALLS_PER_SECOND,
            )
        return len(targets)
