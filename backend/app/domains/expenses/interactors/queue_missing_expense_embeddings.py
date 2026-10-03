"""Queue a vector for expenses that have none. Run by the
`expenses.backfill_embeddings` job (sub-plan 4.3, after reminders')."""

from collections.abc import Callable
from datetime import datetime, timedelta
from uuid import UUID

from app.domains.expenses.constants import (
    BACKFILL_CALLS_PER_SECOND,
    EMBEDDING_BACKFILL_BATCH,
    EMBEDDING_BACKFILL_WINDOW_HOURS,
)
from app.domains.expenses.interactors.dtos import (
    QueueMissingExpenseEmbeddingsInputDTO,
)
from app.domains.expenses.interfaces.dtos import ExpenseEmbeddingTargetDTO
from app.domains.expenses.interfaces.ports import ExpenseEmbedQueue
from app.domains.expenses.interfaces.repositories import ExpenseRepository


class QueueMissingExpenseEmbeddingsInteractor:
    def __init__(
        self,
        *,
        expense_repository: ExpenseRepository,
        embed_queue: ExpenseEmbedQueue,
        now_provider: Callable[[], datetime],
    ) -> None:
        self.expense_repository = expense_repository
        self.embed_queue = embed_queue
        self.now_provider = now_provider

    async def queue_missing_expense_embeddings(
        self, *, dto: QueueMissingExpenseEmbeddingsInputDTO
    ) -> int:
        """Returns how many expenses were handed to the queue.

        The periodic sweep queues one batch of recently touched expenses. The
        full sweep, run once at deploy, walks every expense with no vector and
        spaces the jobs out. The queue's lock keeps an expense already waiting
        from being queued twice."""
        if dto.full:
            return await self._queue_every_missing_expense()
        recent = await self.expense_repository.select_missing_embeddings(
            updated_since=self.now_provider()
            - timedelta(hours=EMBEDDING_BACKFILL_WINDOW_HOURS),
            after_id=None,
            limit=EMBEDDING_BACKFILL_BATCH,
        )
        return await self._queue_targets(targets=recent, first_position=0)

    async def _queue_every_missing_expense(self) -> int:
        queued_count = 0
        after_id: UUID | None = None
        while True:
            page = await self.expense_repository.select_missing_embeddings(
                updated_since=None, after_id=after_id, limit=EMBEDDING_BACKFILL_BATCH
            )
            if not page:
                return queued_count
            queued_count += await self._queue_targets(
                targets=page, first_position=queued_count
            )
            after_id = page[-1].expense_id

    async def _queue_targets(
        self, *, targets: list[ExpenseEmbeddingTargetDTO], first_position: int
    ) -> int:
        for offset, target in enumerate(targets):
            await self.embed_queue.queue_expense_embed(
                user_id=target.user_id,
                expense_id=target.expense_id,
                delay_seconds=(first_position + offset) // BACKFILL_CALLS_PER_SECOND,
            )
        return len(targets)
