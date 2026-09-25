"""Data crossing capture's own boundaries. Frozen, never a model instance."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

from app.domains.reminders.public import ReminderDTO

MissingField = Literal["title", "due_at", "remind_at"]


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


@dataclass(frozen=True)
class NonCommandGuidanceDTO:
    original_input: str


@dataclass(frozen=True)
class UnrecognisedCommandDTO:
    attempted_name: str
    closest_matches: list[str]


CaptureTurnOutcome = Literal[
    "task_created", "question_asked", "discarded", "refused", "reminder_created"
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


@dataclass(frozen=True)
class CaptureHistoryPageDTO:
    items: list[CaptureTurnDTO]
    next_cursor: str | None


@dataclass(frozen=True)
class ReminderListDTO:
    """`/reminders`. Wrapped so it is not confused with `/tasks`' plain list."""

    reminders: list[ReminderDTO]
