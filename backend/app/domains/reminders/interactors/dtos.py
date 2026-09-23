"""Input DTOs, one per use case."""

from dataclasses import dataclass
from datetime import date, time
from uuid import UUID

from app.domains.reminders.services.schedule import RepeatKind


@dataclass(frozen=True)
class GetReminderInputDTO:
    user_id: UUID
    reminder_id: UUID


@dataclass(frozen=True)
class ListRemindersInputDTO:
    user_id: UUID
    search: str | None


@dataclass(frozen=True)
class UpdateReminderInputDTO:
    """The edit form, whole. FR-28: an edit replaces the series' schedule."""

    user_id: UUID
    reminder_id: UUID
    description: str
    start_date: date
    local_time: time
    repeat_kind: RepeatKind
    repeat_interval: int
    repeat_weekdays: tuple[int, ...]


@dataclass(frozen=True)
class DeleteReminderInputDTO:
    user_id: UUID
    reminder_id: UUID
