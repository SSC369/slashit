"""What capture needs from other domains, in its own words.

Per repo-rules.md section 6, the port belongs to the consumer. Neither
Protocol names ``records`` or ``gateway``; each names the one thing capture
needs, in capture's vocabulary.
"""

from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from app.domains.gateway.public import (
    ExtractionResult,
    MalformedResult,
    ProviderTimeout,
    ProviderUnavailable,
    SharedQuotaExhausted,
    UserLimitReached,
)
from app.domains.memories.public import (
    MemoryListDTO,
    MemorySavedDTO,
    MemoryTooLongDTO,
)
from app.domains.records.public import TaskDTO
from app.domains.reminders.public import (
    ReminderDTO,
    ReminderFields,
    ReminderLimitReached,
    ReminderNeedsWhen,
)


class TaskPort(Protocol):
    """What capture needs from records: create one task, list a user's open
    ones for `/tasks`. Named for what it does, not for the domain it reaches.
    """

    async def create_task(
        self,
        *,
        user_id: UUID,
        title: str,
        due_at: datetime | None,
        original_input: str,
    ) -> TaskDTO: ...

    async def list_open_tasks(self, *, user_id: UUID) -> list[TaskDTO]: ...


class ExtractionPort(Protocol):
    async def extract(
        self,
        *,
        user_id: UUID,
        prompt: str,
        schema: dict[str, Any],
        instruction: str,
    ) -> ExtractionResult: ...


class AnalyticsPort(Protocol):
    """What capture needs from analytics: log a no-command session. FR-9's
    metric (PRD section 8) has no other data source."""

    async def record_no_command_input(self, *, user_id: UUID) -> None: ...


class ReminderPort(Protocol):
    """What capture needs from reminders: create one from what a sentence
    said, and list the active ones for `/reminders` (epic 003, FR-1, FR-25)."""

    async def create_reminder(
        self, *, user_id: UUID, fields: ReminderFields, original_input: str
    ) -> ReminderDTO | ReminderLimitReached | ReminderNeedsWhen: ...

    async def list_active(self, *, user_id: UUID) -> list[ReminderDTO]: ...


class LocalClockPort(Protocol):
    """The user's local now and zone name. Every extraction reads relative
    dates against it, tasks included (epic 003, build plan AD-7)."""

    async def local_now(self, *, user_id: UUID) -> tuple[datetime, str]: ...


MemorySaveOutcome = (
    MemorySavedDTO
    | MemoryTooLongDTO
    | UserLimitReached
    | ProviderUnavailable
    | ProviderTimeout
    | SharedQuotaExhausted
    | MalformedResult
)


class MemoryPort(Protocol):
    """What capture needs from memories (epic 004): save a fact, list them,
    look one up. A model failure arrives as the gateway's own member, so the
    client shows the same refusal it shows for a task (FR-9)."""

    async def save_memory(
        self, *, user_id: UUID, text: str, original_input: str
    ) -> MemorySaveOutcome: ...

    async def list_memories(self, *, user_id: UUID) -> MemoryListDTO: ...

    async def look_up_memories(self, *, user_id: UUID, text: str) -> MemoryListDTO: ...
