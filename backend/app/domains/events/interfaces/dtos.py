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
# FR-19 and FR-33: why an alert was not set.
AlertNotSetReasonValue = Literal["passed", "cap"]


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
    alerts_pending: bool = False


@dataclass(frozen=True)
class EventAlertDTO:
    """One alert of the next or only occurrence (FR-14, FR-27)."""

    lead_minutes: int
    text: str
    fires_at: datetime


@dataclass(frozen=True)
class AlertNotSetDTO:
    """An alert asked for and not set, and why (FR-19, FR-33)."""

    lead_minutes: int
    text: str
    reason: AlertNotSetReasonValue


@dataclass(frozen=True)
class EventAlertToSet:
    """What events hands its alerts port for one alert."""

    lead_minutes: int
    fires_at: datetime
    detail: str


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
    origin: RecordOriginValue
    original_input: str | None
    created_at: datetime
    updated_at: datetime
    # Set only on the event a create returns: each rule that changed or
    # inferred something (design §8). Never stored.
    when_notes: tuple[str, ...] = ()
    # Every stored lead, soonest-firing first (FR-14, FR-27).
    alerts: tuple[EventAlertDTO, ...] = ()
    # Set only on a create or an edit: alerts asked for and not set (FR-19,
    # FR-33), and "named twice, kept once" (FR-34). Never stored.
    alerts_not_set: tuple[AlertNotSetDTO, ...] = ()
    alert_notes: tuple[str, ...] = ()


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
    # True when reminders must be given a new set of alerts (dev log D-20).
    alerts_pending: bool


@dataclass(frozen=True)
class EventTargetDTO:
    """One event a background job must act on, across users."""

    user_id: UUID
    event_id: UUID


@dataclass(frozen=True)
class EventText:
    """What an event's meaning vector is made from (FR-30): the words the
    user gave it. A vector is stored only while these are unchanged."""

    title: str
    location: str | None
    description: str | None

    def as_embedding_input(self) -> str:
        return " · ".join(
            part for part in (self.title, self.location, self.description) if part
        )


@dataclass(frozen=True)
class StoredEventMatchDTO:
    """One event a search matched, with the scores search ranks by (005
    AD-3). ``word_rank`` is None when no term is present; ``distance`` is None
    when the event has no vector yet or the search had none."""

    event: StoredEventDTO
    all_terms: bool
    word_rank: float | None
    distance: float | None


@dataclass(frozen=True)
class StoredEventSearchPageDTO:
    matches: list[StoredEventMatchDTO]
    total: int


@dataclass(frozen=True)
class EventEdit:
    """The edit form, whole (FR-28), in the user's own local terms."""

    title: str
    location: str | None
    description: str | None
    start_date: date
    start_time: time | None
    end_date: date | None
    end_time: time | None
    repeat_yearly: bool
    alert_leads_minutes: tuple[int, ...]


@dataclass(frozen=True)
class EventSearchMatchDTO:
    """A search match as every caller reads it: the event, presented."""

    event: EventDTO
    all_terms: bool
    word_rank: float | None
    distance: float | None


@dataclass(frozen=True)
class EventSearchPageDTO:
    matches: list[EventSearchMatchDTO]
    total: int


@dataclass(frozen=True)
class EventUpdatedDTO:
    """FR-28, with each alert asked for and not set (FR-19, FR-33)."""

    event: EventDTO
    alerts_not_set: tuple[AlertNotSetDTO, ...]


@dataclass(frozen=True)
class EventLimitReached:
    """FR-31: the create was refused; nothing was written."""

    limit: int


@dataclass(frozen=True)
class EventNeedsDate:
    """FR-2: no date was said. Nothing was written; the caller asks when."""

    title: str


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


@strawberry.enum
class AlertNotSetReason(Enum):
    PASSED = "passed"
    CAP = "cap"


@strawberry.type
class EventAlert:
    lead_minutes: int
    text: str
    fires_at: datetime


@strawberry.type
class EventAlertNotSet:
    """FR-19 and FR-33: an alert asked for and not set. The event was saved."""

    lead_minutes: int
    text: str
    reason: AlertNotSetReason


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
    origin: str
    original_input: str | None
    created_at: datetime
    updated_at: datetime
    when_notes: list[str] = strawberry.field(
        default_factory=list,
        description="Why the schedule reads as it does. Only on create.",
    )
    alerts: list[EventAlert] = strawberry.field(
        default_factory=list, description="Every alert, soonest-firing first."
    )
    alert_notes: list[str] = strawberry.field(
        default_factory=list,
        description="How the alerts were read, as a lead named twice. Only on create.",
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
        origin=event.origin,
        original_input=event.original_input,
        created_at=event.created_at,
        updated_at=event.updated_at,
        when_notes=list(event.when_notes),
        alerts=[
            EventAlert(
                lead_minutes=alert.lead_minutes,
                text=alert.text,
                fires_at=alert.fires_at,
            )
            for alert in event.alerts
        ],
        alert_notes=list(event.alert_notes),
    )


def alert_not_set_to_type(*, alert_not_set: AlertNotSetDTO) -> EventAlertNotSet:
    return EventAlertNotSet(
        lead_minutes=alert_not_set.lead_minutes,
        text=alert_not_set.text,
        reason=AlertNotSetReason(alert_not_set.reason),
    )


def _clock_text(*, moment: time | None) -> str | None:
    return f"{moment:%H:%M}" if moment is not None else None
