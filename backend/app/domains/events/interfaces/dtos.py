"""Data crossing the events domain's boundaries. Frozen, never a model.

``Event``, the GraphQL shape, lives here rather than under ``graphql/`` so it
may cross into ``capture`` and ``records`` through ``public.py``, the
placement reminders uses for ``Reminder`` (repo-rules.md section 6.2).
"""

from dataclasses import dataclass
from datetime import date, datetime, time
from enum import Enum
from typing import Literal
from uuid import UUID

import strawberry

from app.domains.events.services.schedule import EventStatus, LocalSchedule

RecordOriginValue = Literal["command", "edit"]


@dataclass(frozen=True)
class EventFields:
    """What a sentence said, before any rule is applied (FR-1). Every field
    but the title is optional, because people leave things out (FR-2)."""

    title: str
    start_date: date | None
    has_year: bool
    start_time: time | None
    end_date: date | None
    end_time: time | None
    location: str | None
    description: str | None
    repeat_yearly: bool
    alert_leads_minutes: tuple[int, ...]


@dataclass(frozen=True)
class StoredEventDTO:
    """One row, as storage returns it. ``EventDTO`` adds what depends on now."""

    id: UUID
    user_id: UUID
    title: str
    location: str | None
    description: str | None
    schedule: LocalSchedule
    starts_at: datetime
    ends_at: datetime
    alert_leads_minutes: tuple[int, ...]
    origin: RecordOriginValue
    original_input: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class EventDTO:
    """One event, as every layer above the repository sees it."""

    id: UUID
    user_id: UUID
    title: str
    location: str | None
    description: str | None
    schedule: LocalSchedule
    starts_at: datetime
    ends_at: datetime
    occurrence_date: date
    occurrence_end_date: date
    status: EventStatus
    when_text: str
    alert_lead_minutes: int | None
    alert_text: str | None
    alert_fires_at: datetime | None
    origin: RecordOriginValue
    original_input: str | None
    created_at: datetime
    updated_at: datetime
    # Set only on the event a create returns: each rule that changed or
    # inferred something (design §8). Never stored.
    when_notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class EventWrite:
    """A new event's columns, ready to store."""

    title: str
    location: str | None
    description: str | None
    schedule: LocalSchedule
    starts_at: datetime
    ends_at: datetime
    alert_leads_minutes: tuple[int, ...]
    origin: RecordOriginValue
    original_input: str | None


@dataclass(frozen=True)
class EventLimitReached:
    """FR-31: the create was refused; nothing was written."""

    limit: int


@dataclass(frozen=True)
class EventNeedsDate:
    """FR-2: no date was said. Nothing was written; the caller asks when."""

    title: str


@dataclass(frozen=True)
class AlertChoiceDTO:
    lead_minutes: int
    label: str


@dataclass(frozen=True)
class EventNeedsAlertChoice:
    """FR-16: more than one alert was said. Nothing was written; the caller
    asks which one to keep."""

    title: str
    choices: tuple[AlertChoiceDTO, ...]


@dataclass(frozen=True)
class UserClockDTO:
    """What events needs from identity: where the user is, and the time an
    all-day event's alert counts back from (FR-15)."""

    timezone: str
    default_reminder_time: time


@strawberry.enum
class EventStatusType(Enum):
    UPCOMING = "upcoming"
    HAPPENING_NOW = "happening_now"
    PAST = "past"


@strawberry.type
class Event:
    """The crossable GraphQL shape, build plan §4."""

    id: strawberry.ID
    title: str
    location: str | None
    description: str | None
    start_date: date
    start_time: str | None
    end_date: date | None
    end_time: str | None
    all_day: bool
    repeat_yearly: bool
    schedule_timezone: str
    starts_at: datetime
    ends_at: datetime
    occurrence_date: date
    occurrence_end_date: date
    status: EventStatusType
    when_text: str
    alert_lead_minutes: int | None
    alert_text: str | None
    alert_fires_at: datetime | None
    origin: str
    original_input: str | None
    created_at: datetime
    updated_at: datetime
    when_notes: list[str] = strawberry.field(
        default_factory=list,
        description="Why the schedule reads as it does. Only on create.",
    )


def event_dto_to_type(*, event: EventDTO) -> Event:
    schedule = event.schedule
    return Event(
        id=strawberry.ID(str(event.id)),
        title=event.title,
        location=event.location,
        description=event.description,
        start_date=schedule.start_date,
        start_time=_clock_text(moment=schedule.start_time),
        end_date=schedule.end_date,
        end_time=_clock_text(moment=schedule.end_time),
        all_day=schedule.start_time is None,
        repeat_yearly=schedule.repeat_yearly,
        schedule_timezone=schedule.timezone,
        starts_at=event.starts_at,
        ends_at=event.ends_at,
        occurrence_date=event.occurrence_date,
        occurrence_end_date=event.occurrence_end_date,
        status=EventStatusType(event.status.value),
        when_text=event.when_text,
        alert_lead_minutes=event.alert_lead_minutes,
        alert_text=event.alert_text,
        alert_fires_at=event.alert_fires_at,
        origin=event.origin,
        original_input=event.original_input,
        created_at=event.created_at,
        updated_at=event.updated_at,
        when_notes=list(event.when_notes),
    )


def _clock_text(*, moment: time | None) -> str | None:
    return f"{moment:%H:%M}" if moment is not None else None
