"""An event's schedule: local fields in, UTC instants and words out.

Pure: no I/O, no clock of its own. Every date rule of PRD FR-3 to FR-7,
FR-10, FR-12 and FR-25 lives here, so it is tested once (build plan AD-2,
AD-6). The stored truth is the local fields plus the zone they were set in;
``starts_at`` and ``ends_at`` are derived from them for the next or only
occurrence.
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from enum import StrEnum
from zoneinfo import ZoneInfo

from app.domains.events.constants import (
    MINUTES_PER_DAY,
    MINUTES_PER_HOUR,
    MINUTES_PER_WEEK,
)

_FEBRUARY = 2
_LEAP_DAY = 29


class EventStatus(StrEnum):
    UPCOMING = "upcoming"
    HAPPENING_NOW = "happening_now"
    PAST = "past"


@dataclass(frozen=True)
class LocalSchedule:
    """What the user said, in their own local terms. ``start_time`` None is
    all-day (FR-3). ``end_date`` is set for a multi-day or overnight event."""

    start_date: date
    start_time: time | None
    end_date: date | None
    end_time: time | None
    repeat_yearly: bool
    timezone: str


@dataclass(frozen=True)
class Resolved:
    """The next or only occurrence. ``occurrence_date`` is its local start."""

    starts_at: datetime
    ends_at: datetime
    occurrence_date: date
    occurrence_end_date: date


@dataclass(frozen=True)
class SaidSchedule:
    """The model's reading of a sentence, before any rule is applied."""

    start_date: date
    has_year: bool
    start_time: time | None
    end_date: date | None
    end_time: time | None
    repeat_yearly: bool


@dataclass(frozen=True)
class NormalisedSchedule:
    """A schedule ready to store, and the notes the confirmation shows for
    each rule that changed or inferred something (design §8)."""

    start_date: date
    start_time: time | None
    end_date: date | None
    end_time: time | None
    repeat_yearly: bool
    notes: tuple[str, ...]


def normalise_said_schedule(
    *, said: SaidSchedule, local_today: date
) -> NormalisedSchedule:
    """Apply the capture rules: FR-3 all-day, FR-4 a passed date with no year
    moves to next year, FR-5 a stated past year is kept, FR-6 a date range,
    FR-7 an end time before the start time ends the next day."""
    notes: list[str] = []
    start_date = said.start_date
    if not said.has_year and start_date < local_today:
        start_date = _next_year_on_or_after(day=start_date, earliest=local_today)
        notes.append(
            f"{_day_month(day=said.start_date)} has passed this year, so next year"
        )
    elif said.has_year and not said.repeat_yearly and start_date < local_today:
        notes.append("A past date, saved as given")

    start_time = said.start_time
    end_time = said.end_time if start_time is not None else None
    end_date = _read_end_date(said=said, start_date=start_date)
    if start_time is None:
        notes.append("No time given, so all day")
    elif end_time is not None and end_date is None and end_time < start_time:
        end_date = start_date + timedelta(days=1)
        notes.append(
            f"Ends after midnight, so on {_day_label(day=end_date, today=None)}"
        )

    if said.repeat_yearly and (start_date.month, start_date.day) == (
        _FEBRUARY,
        _LEAP_DAY,
    ):
        notes.append("Feb 29 in leap years, Feb 28 otherwise")
    return NormalisedSchedule(
        start_date=start_date,
        start_time=start_time,
        end_date=end_date,
        end_time=end_time,
        repeat_yearly=said.repeat_yearly,
        notes=tuple(notes),
    )


def resolve(*, schedule: LocalSchedule, now: datetime) -> Resolved:
    """The next or only occurrence as UTC instants. A one-time event resolves
    to its own date, past or not. A yearly event resolves to the first
    occurrence that has not yet ended."""
    if not schedule.repeat_yearly:
        return _resolve_on(schedule=schedule, occurrence_date=schedule.start_date)
    zone = ZoneInfo(schedule.timezone)
    first_year = max(schedule.start_date.year, now.astimezone(zone).year - 1)
    for year in range(first_year, first_year + 3):
        resolved = _resolve_on(
            schedule=schedule,
            occurrence_date=_on_year(day=schedule.start_date, year=year),
        )
        if resolved.ends_at > now:
            return resolved
    return resolved


def event_status(*, resolved: Resolved, now: datetime) -> EventStatus:
    """FR-25 and design Q3: upcoming, happening between start and end, past."""
    if now < resolved.starts_at:
        return EventStatus.UPCOMING
    if now < resolved.ends_at:
        return EventStatus.HAPPENING_NOW
    return EventStatus.PAST


def describe_when(
    *, schedule: LocalSchedule, resolved: Resolved, local_today: date
) -> str:
    """The When line, as design §8 writes it: "Mon 12 Oct, all day",
    "Fri 9 Oct, 4:00 to 5:00 PM", "Sun 20 to Thu 24 Dec, all day"."""
    start_label = _day_label(day=resolved.occurrence_date, today=local_today)
    is_multi_day = resolved.occurrence_end_date != resolved.occurrence_date
    if schedule.start_time is None:
        if not is_multi_day:
            return f"{start_label}, all day"
        range_label = _range_label(
            start=resolved.occurrence_date,
            end=resolved.occurrence_end_date,
            today=local_today,
        )
        return f"{range_label}, all day"
    start_text = _clock(moment=schedule.start_time)
    if schedule.end_time is None:
        return f"{start_label}, {start_text}"
    end_text = _clock(moment=schedule.end_time)
    days_apart = (resolved.occurrence_end_date - resolved.occurrence_date).days
    if days_apart > 1:
        end_label = _day_label(day=resolved.occurrence_end_date, today=local_today)
        return f"{start_label}, {start_text} to {end_label}, {end_text}"
    if days_apart == 0 and start_text[-2:] == end_text[-2:]:
        start_text = start_text[:-3]
    return f"{start_label}, {start_text} to {end_text}"


def describe_alert(*, lead_minutes: int) -> str:
    """ "1 day before", "1 hour before", "At start"."""
    if lead_minutes == 0:
        return "At start"
    for unit_minutes, unit_name in (
        (MINUTES_PER_WEEK, "week"),
        (MINUTES_PER_DAY, "day"),
        (MINUTES_PER_HOUR, "hour"),
    ):
        if lead_minutes % unit_minutes == 0:
            count = lead_minutes // unit_minutes
            return f"{count} {unit_name}{'' if count == 1 else 's'} before"
    return f"{lead_minutes} minute{'' if lead_minutes == 1 else 's'} before"


def alert_fires_at(
    *,
    schedule: LocalSchedule,
    resolved: Resolved,
    lead_minutes: int,
    default_reminder_time: time,
) -> datetime:
    """FR-14 and FR-15: a timed event counts back from its start; an all-day
    one from the default reminder time on its date."""
    lead = timedelta(minutes=lead_minutes)
    if schedule.start_time is not None:
        return resolved.starts_at - lead
    zone = ZoneInfo(schedule.timezone)
    reference = datetime.combine(
        resolved.occurrence_date, default_reminder_time, tzinfo=zone
    )
    return reference - lead


def _resolve_on(*, schedule: LocalSchedule, occurrence_date: date) -> Resolved:
    zone = ZoneInfo(schedule.timezone)
    span_days = (
        (schedule.end_date - schedule.start_date).days if schedule.end_date else 0
    )
    end_date = occurrence_date + timedelta(days=span_days)
    if schedule.start_time is None:
        starts_at = datetime.combine(occurrence_date, time(0), tzinfo=zone)
        ends_at = datetime.combine(end_date + timedelta(days=1), time(0), tzinfo=zone)
    else:
        starts_at = datetime.combine(occurrence_date, schedule.start_time, tzinfo=zone)
        ends_at = _timed_end(
            schedule=schedule, end_date=end_date, zone=zone, starts_at=starts_at
        )
    return Resolved(
        starts_at=starts_at.astimezone(ZoneInfo("UTC")),
        ends_at=ends_at.astimezone(ZoneInfo("UTC")),
        occurrence_date=occurrence_date,
        occurrence_end_date=end_date,
    )


def _timed_end(
    *, schedule: LocalSchedule, end_date: date, zone: ZoneInfo, starts_at: datetime
) -> datetime:
    """A timed event with no end lasts until local midnight, so it stays
    listed for the rest of its day (FR-25)."""
    if schedule.end_time is None:
        return datetime.combine(end_date + timedelta(days=1), time(0), tzinfo=zone)
    ends_at = datetime.combine(end_date, schedule.end_time, tzinfo=zone)
    return max(ends_at, starts_at)


def _read_end_date(*, said: SaidSchedule, start_date: date) -> date | None:
    """A range end keeps the start's shift to next year. An end that still
    falls before the start ("Dec 28 to Jan 2") is in the following year; one
    that cannot be made to follow it is dropped rather than refused."""
    if said.end_date is None:
        return None
    end_date = said.end_date + (start_date - said.start_date)
    if end_date < start_date and not said.has_year:
        end_date = _on_year(day=end_date, year=end_date.year + 1)
    if end_date <= start_date:
        return None
    return end_date


def _next_year_on_or_after(*, day: date, earliest: date) -> date:
    year = earliest.year
    candidate = _on_year(day=day, year=year)
    if candidate < earliest:
        candidate = _on_year(day=day, year=year + 1)
    return candidate


def _on_year(*, day: date, year: int) -> date:
    """FR-10: February 29 falls on February 28 in a common year."""
    try:
        return day.replace(year=year)
    except ValueError:
        return date(year, _FEBRUARY, _LEAP_DAY - 1)


def _range_label(*, start: date, end: date, today: date) -> str:
    if start.year == end.year and start.month == end.month and start != today:
        return f"{start:%a} {start.day} to {_day_label(day=end, today=today)}"
    return f"{_day_label(day=start, today=today)} to {_day_label(day=end, today=today)}"


def _day_label(*, day: date, today: date | None) -> str:
    if today is not None and day == today:
        return "Today"
    if today is not None and day == today + timedelta(days=1):
        return "Tomorrow"
    label = f"{day:%a} {day.day} {day:%b}"
    if today is not None and day.year != today.year:
        label = f"{label} {day.year}"
    return label


def _day_month(*, day: date) -> str:
    return f"{day.day} {day:%b}"


def _clock(*, moment: time) -> str:
    hour = moment.hour % 12 or 12
    meridiem = "AM" if moment.hour < 12 else "PM"
    return f"{hour}:{moment.minute:02d} {meridiem}"
