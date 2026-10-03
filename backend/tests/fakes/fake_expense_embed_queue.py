"""An in-memory ExpenseEmbedQueue that records what was queued."""

import uuid


class FakeExpenseEmbedQueue:
    def __init__(self) -> None:
        self.queued: list[tuple[uuid.UUID, uuid.UUID, int]] = []

    async def queue_expense_embed(
        self, *, user_id: uuid.UUID, expense_id: uuid.UUID, delay_seconds: int
    ) -> None:
        self.queued.append((user_id, expense_id, delay_seconds))
