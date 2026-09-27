"""Queue a vector for every recent memory that has none. Run by the
`memories.backfill_embeddings` job (004 P-6)."""

from collections.abc import Callable
from datetime import datetime, timedelta

from app.domains.memories.constants import (
    EMBEDDING_BACKFILL_BATCH,
    EMBEDDING_BACKFILL_WINDOW_HOURS,
)
from app.domains.memories.interfaces.ports import ReembedQueue
from app.domains.memories.interfaces.repositories import MemoryRepository


class QueueMissingEmbeddingsInteractor:
    def __init__(
        self,
        *,
        memory_repository: MemoryRepository,
        reembed_queue: ReembedQueue,
        now_provider: Callable[[], datetime],
    ) -> None:
        self.memory_repository = memory_repository
        self.reembed_queue = reembed_queue
        self.now_provider = now_provider

    async def queue_missing_embeddings(self) -> int:
        """Returns how many memories were handed to the queue. The queue's lock
        keeps a memory already waiting from being queued twice."""
        missing = await self.memory_repository.select_missing_embeddings(
            updated_since=self.now_provider()
            - timedelta(hours=EMBEDDING_BACKFILL_WINDOW_HOURS),
            limit=EMBEDDING_BACKFILL_BATCH,
        )
        for memory in missing:
            await self.reembed_queue.enqueue_reembed(
                user_id=memory.user_id, memory_id=memory.memory_id
            )
        return len(missing)
