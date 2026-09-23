"""Data crossing the reminders domain's boundaries. Frozen, never a model.

``Reminder``, the GraphQL shape, lives here rather than under ``graphql/`` so
it may cross into ``capture`` and ``records`` through ``public.py``, the same
placement ``records`` uses for ``Task`` (repo-rules.md section 6.2).
"""

from dataclasses import dataclass
from datetime import date, datetime, time
from enum import Enum
from typing import Literal
from uuid import UUID

import strawberry

from app.domains.reminders.services.schedule import (
    RepeatKind,
    ScheduleSpec,
    ScheduleSummary,
)

ReminderStateValue = Literal["upcoming", "fired", "done"]
ReminderActionValue = Literal["done", "snoozed", "missed"]
RecordOriginValue = Literal["command", "edit"]


@dataclass(frozen=True)
class ReminderDTO:
    """One reminder, as every layer above the repository sees it."""

    id: UUID
    user_id: UUID
    description: str
    spec: ScheduleSpec
    schedule_timezone: str
    next_fire_at: datetime | None
    state: ReminderStateValue
    last_fired_at: datetime | None
    last_action: ReminderActionValue | None
    summary: ScheduleSummary
    origin: RecordOriginValue
    original_input: str | None
    created_at: datetime
    updated_at: datetime
    # Set only on the reminder a create returns: why its time differs from
    # what was typed. Never stored, so every read leaves it None.
    when_note: str | None = None


@dataclass(frozen=True)
class ReminderFields:
    """What a sentence said, before any rule is applied. Every field but the
    description is optional, because people leave things out (FR-2, FR-3)."""

    description: str
    local_date: date | None
    local_time: time | None
    repeat_kind: RepeatKind
    repeat_interval: int
    repeat_weekdays: tuple[int, ...]
    month_day: int | None


@dataclass(frozen=True)
class ReminderLimitReached:
    """FR-38: the create was refused; nothing was written."""

    limit: int


@dataclass(frozen=True)
class ReminderNeedsWhen:
    """FR-2: the sentence set no date the rule can start from. Nothing was
    written; the caller asks one question."""

    description: str


@dataclass(frozen=True)
class ReminderGroupsDTO:
    """FR-26: the Reminders tab's three groups, each already ordered."""

    needs_attention: list[ReminderDTO]
    upcoming: list[ReminderDTO]
    done: list[ReminderDTO]


@dataclass(frozen=True)
class UserClockDTO:
    """What reminders needs from identity: where the user is and their default."""

    timezone: str
    default_reminder_time: time


@strawberry.enum
class ReminderState(Enum):
    UPCOMING = "upcoming"
    FIRED = "fired"
    DONE = "done"


@strawberry.enum
class ReminderRepeatKind(Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


@strawberry.enum
class ReminderAction(Enum):
    DONE = "done"
    SNOOZED = "snoozed"
    MISSED = "missed"


@strawberry.type
class Reminder:
    """The crossable GraphQL shape, index §4."""

    id: strawberry.ID
    description: str
    state: ReminderState
    next_fire_at: datetime | None
    when_text: str
    repeat_text: str
    repeat_kind: ReminderRepeatKind
    repeat_interval: int
    repeat_weekdays: list[int]
    repeat_month_day: int | None
    local_time: str
    anchor_local_date: date
    schedule_timezone: str
    last_fired_at: datetime | None
    last_action: ReminderAction | None
    origin: str
    original_input: str | None
    created_at: datetime
    updated_at: datetime
    when_note: str | None = strawberry.field(
        default=None,
        description="Why the time differs from what was typed. Only on create.",
    )


def reminder_dto_to_type(*, reminder: ReminderDTO) -> Reminder:
    spec = reminder.spec
    return Reminder(
        id=strawberry.ID(str(reminder.id)),
        description=reminder.description,
        state=ReminderState(reminder.state),
        next_fire_at=reminder.next_fire_at,
        when_text=reminder.summary.when_text,
        repeat_text=reminder.summary.repeat_text,
        repeat_kind=ReminderRepeatKind(spec.repeat_kind.value),
        repeat_interval=spec.repeat_interval,
        repeat_weekdays=list(spec.repeat_weekdays),
        repeat_month_day=spec.repeat_month_day,
        local_time=f"{spec.local_time:%H:%M}",
        anchor_local_date=spec.anchor_local_date,
        schedule_timezone=reminder.schedule_timezone,
        last_fired_at=reminder.last_fired_at,
        last_action=(
            ReminderAction(reminder.last_action) if reminder.last_action else None
        ),
        origin=reminder.origin,
        original_input=reminder.original_input,
        created_at=reminder.created_at,
        updated_at=reminder.updated_at,
        when_note=reminder.when_note,
    )
