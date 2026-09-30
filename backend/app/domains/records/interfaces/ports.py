"""What records needs from other domains, in its own words.

Per repo-rules.md section 6, the port belongs to the consumer.
"""

from typing import Protocol
from uuid import UUID

from app.domains.memories.public import MemoryDTO
from app.domains.reminders.public import ReminderDTO


class AnalyticsPort(Protocol):
    """What records needs from analytics: log a records view being opened.
    That metric (PRD section 8) has no other data source."""

    async def record_records_view_opened(self, *, user_id: UUID) -> None: ...


class ReminderRecordsPort(Protocol):
    """What records needs from reminders: every live reminder, for the All
    tab (epic 003, FR-26). Records orders the merged list itself."""

    async def list_reminders(
        self, *, user_id: UUID, search: str | None
    ) -> list[ReminderDTO]: ...


class MemoryRecordsPort(Protocol):
    """What records needs from memories: every live memory, for the All tab
    (epic 004, FR-15). Records orders the merged list itself."""

    async def list_memories(
        self, *, user_id: UUID, search: str | None
    ) -> list[MemoryDTO]: ...


class TaskEmbeddingPort(Protocol):
    """What records needs to give a task a meaning vector (epic 005 AD-7).
    None when the model refused; the job then retries."""

    async def embed_task_title(
        self, *, user_id: UUID, title: str
    ) -> tuple[float, ...] | None: ...


class TaskEmbedQueue(Protocol):
    """Queues a task's vector after a create or a title edit, so neither
    waits on, or fails with, the model (005 build plan §7)."""

    async def queue_task_embed(
        self, *, user_id: UUID, task_id: UUID, delay_seconds: int
    ) -> None: ...
