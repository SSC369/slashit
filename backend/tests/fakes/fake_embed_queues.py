"""In-memory embed queues for tasks and reminders (epic 005 AD-7).

Each records what was queued, so a test can assert a create or an edit asked
for a vector, and with what spacing a backfill sweep did it.
"""

from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class FakeTaskEmbedQueue:
    queued: list[tuple[UUID, UUID, int]] = field(default_factory=list)

    async def queue_task_embed(
        self, *, user_id: UUID, task_id: UUID, delay_seconds: int
    ) -> None:
        self.queued.append((user_id, task_id, delay_seconds))


@dataclass
class FakeReminderEmbedQueue:
    queued: list[tuple[UUID, UUID, int]] = field(default_factory=list)

    async def queue_reminder_embed(
        self, *, user_id: UUID, reminder_id: UUID, delay_seconds: int
    ) -> None:
        self.queued.append((user_id, reminder_id, delay_seconds))
