"""Data crossing capture's own boundaries. Frozen, never a model instance."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

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
]


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


@dataclass(frozen=True)
class CaptureHistoryPageDTO:
    items: list[CaptureTurnDTO]
    next_cursor: str | None


@dataclass(frozen=True)
class ReminderListDTO:
    """`/reminders`. Wrapped so it is not confused with `/tasks`' plain list."""

    reminders: list[ReminderDTO]
