"""What capture needs from other domains, in its own words.

Per repo-rules.md section 6, the port belongs to the consumer. Neither
Protocol names ``records`` or ``gateway``; each names the one thing capture
needs, in capture's vocabulary.
"""

from datetime import datetime
from typing import Any, Literal, Protocol
from uuid import UUID

from app.domains.events.public import (
    EventDTO,
    EventFields,
    EventLimitReached,
    EventNeedsAlertChoice,
    EventNeedsDate,
)
from app.domains.expenses.public import (
    ExpenseDTO,
    ExpenseFields,
    ExpenseSummaryDTO,
    PeriodNotUnderstood,
)
from app.domains.gateway.public import (
    ExtractionResult,
    MalformedResult,
    ProviderTimeout,
    ProviderUnavailable,
    SharedQuotaExhausted,
    UserLimitReached,
)
from app.domains.memories.public import (
    ConflictAnswer,
    MemoryCategory,
    MemoryConflictDTO,
    MemoryDiscardedDTO,
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
from app.domains.search.public import SearchResultsDTO


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


ExpenseCaptureEventType = Literal["expense_amount_asked", "expense_currency_refused"]


class AnalyticsPort(Protocol):
    """What capture needs from analytics: log a no-command session. FR-9's
    metric (PRD section 8) has no other data source."""

    async def record_no_command_input(self, *, user_id: UUID) -> None: ...

    async def record_expense_capture_event(
        self, *, user_id: UUID, event_type: ExpenseCaptureEventType, is_choice: bool
    ) -> None:
        """Epic 006, PRD section 8: an amount question or a currency refusal.
        ``is_choice`` tells FR-5's question from FR-3's. Never the text."""
        ...


class ReminderPort(Protocol):
    """What capture needs from reminders: create one from what a sentence
    said, and list the active ones for `/reminders` (epic 003, FR-1, FR-25)."""

    async def create_reminder(
        self, *, user_id: UUID, fields: ReminderFields, original_input: str
    ) -> ReminderDTO | ReminderLimitReached | ReminderNeedsWhen: ...

    async def list_active(self, *, user_id: UUID) -> list[ReminderDTO]: ...


class EventPort(Protocol):
    """What capture needs from events: create one from what a sentence said,
    and list the upcoming ones for `/events` (epic 007, FR-1, FR-24)."""

    async def create_event(
        self, *, user_id: UUID, fields: EventFields, original_input: str
    ) -> EventDTO | EventLimitReached | EventNeedsDate | EventNeedsAlertChoice: ...

    async def list_upcoming(self, *, user_id: UUID) -> list[EventDTO]: ...


class LocalClockPort(Protocol):
    """The user's local now and zone name. Every extraction reads relative
    dates against it, tasks included (epic 003, build plan AD-7)."""

    async def local_now(self, *, user_id: UUID) -> tuple[datetime, str]: ...


MemorySaveOutcome = (
    MemorySavedDTO
    | MemoryConflictDTO
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

    async def resolve_conflict(
        self,
        *,
        user_id: UUID,
        text: str,
        category: MemoryCategory | None,
        original_input: str,
        conflicting_ids: list[UUID],
        answer: ConflictAnswer,
    ) -> MemorySavedDTO | MemoryDiscardedDTO: ...


class SearchPort(Protocol):
    """What capture needs from search: `/search <text>` across every record
    type, grouped and ranked (epic 005, FR-1 to FR-12, FR-20)."""

    async def search(self, *, user_id: UUID, text: str) -> SearchResultsDTO: ...


class ExpensePort(Protocol):
    """What capture needs from expenses: save one it has fully read (epic
    006, FR-1)."""

    async def create_expense(
        self, *, user_id: UUID, fields: ExpenseFields, original_input: str
    ) -> ExpenseDTO: ...

    async def summarise_text(
        self, *, user_id: UUID, text: str
    ) -> ExpenseSummaryDTO | PeriodNotUnderstood:
        """FR-23 to FR-27: `/expenses <period>`, read and summed by expenses."""
        ...
