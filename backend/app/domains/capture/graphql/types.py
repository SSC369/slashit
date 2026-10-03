"""Capture's own success-shaped outcomes.

The five failure-shaped outcomes (UserLimitReached, ProviderUnavailable,
ProviderTimeout, SharedQuotaExhausted, MalformedResult) are not redefined
here: they cross from ``gateway.public`` directly, per build plan section 7
corrected 2026-09-13.
"""

from datetime import date, datetime
from enum import Enum

import strawberry

from app.domains.capture.interfaces.dtos import (
    CaptureTurnDTO,
    ExpenseQuestionKind,
    ExpenseRefusalReason,
)
from app.domains.events.public import Event, EventAlertNotSet
from app.domains.expenses.public import Expense, Paise
from app.domains.memories.public import Memory, MemoryCategory, SecretKind
from app.domains.records.public import Task
from app.domains.reminders.public import Reminder


@strawberry.type
class TaskCreated:
    task: Task


@strawberry.type
class TasksListed:
    """`/tasks`. Its own outcome, not reused from a slice 2 query: this domain
    exists before slice 2's `tasks` GraphQL query does."""

    tasks: list[Task]


@strawberry.type
class ReminderCreated:
    """Epic 003, FR-1, FR-5: the card reads `reminder.whenText` and
    `reminder.repeatText`."""

    reminder: Reminder


@strawberry.type
class RemindersListed:
    """`/reminders`, FR-25: active reminders, soonest first."""

    reminders: list[Reminder]


@strawberry.type
class EventCreated:
    """Epic 007, FR-8: the card reads `event.whenText` and `event.whenNotes`.
    FR-19 and FR-33: each alert asked for and not set, with why."""

    event: Event
    alerts_not_set: list[EventAlertNotSet]


@strawberry.type
class EventsListed:
    """`/events`, FR-24: upcoming events, soonest first."""

    events: list[Event]


@strawberry.type
class EventLimitReached:
    """FR-31. Nothing was saved; the input is kept by the client."""

    message: str
    limit: int


@strawberry.type
class MemorySaved:
    """Epic 004, FR-7 and FR-8: the saved card, and its caution when the fact
    looks like a secret. The caution names the kind, never the text."""

    memory: Memory
    secret_caution: SecretKind | None


@strawberry.type
class MemoriesListed:
    """Epic 004, FR-19 and FR-20. `searchText` is set for `/memories <text>`,
    so the card can say what matched, or that nothing did."""

    memories: list[Memory]
    search_text: str | None


@strawberry.type
class MemoryConflictAsked:
    """Epic 004, FR-10: nothing was saved. The new fact waits beside every
    memory it contradicts until the user answers "Which is correct?"."""

    pending_capture_id: strawberry.ID
    question: str
    new_text: str
    category: MemoryCategory | None
    conflicting: list[Memory]


@strawberry.type
class MemoryDiscarded:
    """FR-11, "Keep the old one": the new fact was dropped, nothing changed."""

    message: str


@strawberry.type
class ExpenseSaved:
    """Epic 006, FR-12: amount, description, category and date, as read."""

    expense: Expense


@strawberry.type
class ExpenseQuestionAsked:
    """Epic 006, FR-3 to FR-5, FR-8: nothing saved. ``amountCandidates`` are
    FR-5's chips; ``readDate`` is the future date FR-8 asks to confirm."""

    pending_capture_id: strawberry.ID
    kind: ExpenseQuestionKind
    question: str
    amount_candidates: list[Paise]
    read_date: date | None


@strawberry.type
class ExpenseRefused:
    """Epic 006, FR-6 and FR-13: nothing saved; the client keeps the text."""

    message: str
    reason: ExpenseRefusalReason
    length: int | None


@strawberry.type
class PendingCaptureNotFound:
    """The conflict was already answered or discarded, from another tab or
    device. This request changed nothing (FR-13)."""

    message: str


@strawberry.type
class ReminderLimitReached:
    """FR-38. Nothing was saved; the input is kept by the client."""

    message: str
    limit: int


@strawberry.type
class PendingQuestionCreated:
    pending_capture_id: strawberry.ID
    question: str


@strawberry.type
class NonCommandGuidance:
    original_input: str


@strawberry.type
class UnrecognisedCommand:
    attempted_name: str
    closest_matches: list[str]


@strawberry.enum
class CaptureTurnOutcome(Enum):
    TASK_CREATED = "task_created"
    QUESTION_ASKED = "question_asked"
    DISCARDED = "discarded"
    REFUSED = "refused"
    REMINDER_CREATED = "reminder_created"
    MEMORY_SAVED = "memory_saved"
    MEMORY_LISTED = "memory_listed"
    MEMORY_FORGOTTEN = "memory_forgotten"
    MEMORY_CONFLICT_RESOLVED = "memory_conflict_resolved"
    # Epic 005, FR-21.
    SEARCHED = "searched"
    # Epic 007.
    EVENT_CREATED = "event_created"
    EVENTS_LISTED = "events_listed"
    # Epic 006.
    EXPENSE_SAVED = "expense_saved"
    EXPENSES_SUMMARISED = "expenses_summarised"


@strawberry.type
class CaptureTurn:
    id: strawberry.ID
    input_text: str
    outcome: CaptureTurnOutcome
    resulting_task_id: strawberry.ID | None
    resulting_pending_capture_id: strawberry.ID | None
    resulting_reminder_id: strawberry.ID | None
    resulting_memory_id: strawberry.ID | None
    resulting_event_id: strawberry.ID | None
    resulting_expense_id: strawberry.ID | None
    forgotten: bool
    affected_count: int | None
    question_text: str | None
    answer_text: str | None
    created_at: datetime


@strawberry.type
class CaptureHistoryPage:
    items: list[CaptureTurn]
    next_cursor: str | None


def capture_turn_dto_to_type(*, turn: CaptureTurnDTO) -> CaptureTurn:
    return CaptureTurn(
        id=strawberry.ID(str(turn.id)),
        input_text=turn.input_text,
        outcome=CaptureTurnOutcome(turn.outcome),
        resulting_task_id=(
            strawberry.ID(str(turn.resulting_task_id))
            if turn.resulting_task_id
            else None
        ),
        resulting_pending_capture_id=(
            strawberry.ID(str(turn.resulting_pending_capture_id))
            if turn.resulting_pending_capture_id
            else None
        ),
        resulting_reminder_id=(
            strawberry.ID(str(turn.resulting_reminder_id))
            if turn.resulting_reminder_id
            else None
        ),
        resulting_memory_id=(
            strawberry.ID(str(turn.resulting_memory_id))
            if turn.resulting_memory_id
            else None
        ),
        resulting_event_id=(
            strawberry.ID(str(turn.resulting_event_id))
            if turn.resulting_event_id
            else None
        ),
        resulting_expense_id=(
            strawberry.ID(str(turn.resulting_expense_id))
            if turn.resulting_expense_id
            else None
        ),
        forgotten=turn.forgotten,
        affected_count=turn.affected_count,
        question_text=turn.question_text,
        answer_text=turn.answer_text,
        created_at=turn.created_at,
    )
