"""Data crossing capture's own boundaries. Frozen, never a model instance."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

import strawberry

from app.domains.expenses.public import ExpenseCategory
from app.domains.memories.public import MemoryCategory, MemoryDTO
from app.domains.reminders.public import ReminderDTO

MissingField = Literal[
    "title",
    "due_at",
    "remind_at",
    "fact",
    "memory_conflict",
    # Epic 005, FR-2.
    "search_text",
    # Epic 006, migration 0038: the four expense questions (AD-6).
    "expense_amount",
    "expense_description",
    "expense_amount_choice",
    "expense_date",
]


@strawberry.enum
class ExpenseQuestionKind(StrEnum):
    """Epic 006: the four questions, asked in this order (build plan §5)."""

    AMOUNT = "expense_amount"
    AMOUNT_CHOICE = "expense_amount_choice"
    DESCRIPTION = "expense_description"
    DATE = "expense_date"


@strawberry.enum
class ExpenseRefusalReason(StrEnum):
    """FR-6, FR-13 and, from slice 2, FR-27."""

    FOREIGN_CURRENCY = "foreign_currency"
    DESCRIPTION_TOO_LONG = "description_too_long"
    PERIOD_NOT_UNDERSTOOD = "period_not_understood"


@dataclass(frozen=True)
class ExpenseDraft:
    """What a `/add-expense` has read so far. Held in ``pending_captures``'
    typed ``expense_`` columns while a question waits (AD-6)."""

    amount_paise: int | None = None
    candidates: tuple[int, ...] = ()
    description: str | None = None
    category: ExpenseCategory | None = None
    spent_on: date | None = None


@dataclass(frozen=True)
class PendingCaptureDTO:
    """One unanswered question, waiting on a missing field."""

    id: UUID
    user_id: UUID
    command_name: str
    known_title: str | None
    missing_field: MissingField
    question_text: str
    original_input: str
    asked_at: datetime
    # Epic 004, sub-plan 4.3: set only when ``missing_field`` is
    # ``memory_conflict``. The new fact and the ids it contradicts, never the
    # old memories' text (index §4).
    candidate_text: str | None = None
    candidate_category: MemoryCategory | None = None
    conflicting_memory_ids: tuple[UUID, ...] = ()
    # Epic 006: set only on an expense question. ``known_title`` then holds
    # the words that gave the date, for FR-8's question (dev log D-1).
    expense_draft: ExpenseDraft | None = None


@dataclass(frozen=True)
class MemoryConflictAskedDTO:
    """FR-10: nothing saved; "Which is correct?" waits as a pending conflict.
    ``conflicting`` is read live for the card and never stored by capture."""

    pending_capture_id: UUID
    question: str
    text: str
    category: MemoryCategory | None
    conflicting: list[MemoryDTO]


@dataclass(frozen=True)
class ExpenseQuestionAskedDTO:
    """FR-3 to FR-5, FR-8: nothing saved; one question waits. ``read_date``
    is set on a DATE question, ``amount_candidates`` on an AMOUNT_CHOICE."""

    pending_capture_id: UUID
    kind: ExpenseQuestionKind
    question: str
    amount_candidates: tuple[int, ...]
    read_date: date | None


@dataclass(frozen=True)
class ExpenseRefusedDTO:
    """FR-6, FR-13: nothing saved; the client keeps the text. ``length`` is
    set for an over-long description."""

    reason: ExpenseRefusalReason
    length: int | None = None
    # FR-27: the period text that was not understood, quoted back.
    period_text: str | None = None


@dataclass(frozen=True)
class PendingCaptureGoneDTO:
    """The conflict was already answered or discarded, from another tab."""


@dataclass(frozen=True)
class NonCommandGuidanceDTO:
    original_input: str


@dataclass(frozen=True)
class UnrecognisedCommandDTO:
    attempted_name: str
    closest_matches: list[str]


CaptureTurnOutcome = Literal[
    "task_created",
    "question_asked",
    "discarded",
    "refused",
    "reminder_created",
    # Epic 004, migration 0025.
    "memory_saved",
    "memory_listed",
    "memory_forgotten",
    "memory_conflict_resolved",
    # Epic 005, migration 0034: the typed line only, never results (FR-21).
    "searched",
    # Epic 006, migration 0038. `expenses_summarised` is slice 2's.
    "expense_saved",
    "expenses_summarised",
]


@dataclass(frozen=True)
class CaptureTurnDTO:
    """A logged capture attempt. FR-44: retained after its outcome, so this
    outlives the PendingCaptureDTO it may reference."""

    id: UUID
    input_text: str
    outcome: CaptureTurnOutcome
    resulting_task_id: UUID | None
    resulting_pending_capture_id: UUID | None
    question_text: str | None
    answer_text: str | None
    created_at: datetime
    # Epic 003. Last, with a default, so existing constructions stay valid.
    resulting_reminder_id: UUID | None = None
    # Epic 004. Slice 3's forget scrubs the turns that point at a memory.
    resulting_memory_id: UUID | None = None
    # Epic 004, sub-plan 4.2: a scrubbed turn, and a `/forget` turn's count.
    forgotten: bool = False
    affected_count: int | None = None
    # Epic 006, migration 0038.
    resulting_expense_id: UUID | None = None


@dataclass(frozen=True)
class CaptureHistoryPageDTO:
    items: list[CaptureTurnDTO]
    next_cursor: str | None


@dataclass(frozen=True)
class ReminderListDTO:
    """`/reminders`. Wrapped so it is not confused with `/tasks`' plain list."""

    reminders: list[ReminderDTO]
