"""Schedule maths for reminders. Pure: no I/O, no clock of its own.

Index §4 of the implementation plan. Every fire time in the product comes from
``next_occurrence``: slice 1's create and edit, slice 2's firing job, slice 4's
timezone recompute. It owns FR-8 (month end, 29 February), FR-9 (wall-clock
time across clock changes) and AD-12 (a local time that does not exist fires at
the first valid minute after it; a time that occurs twice fires at the first).

A schedule is kept in local terms (build plan AD-5): a date, a time and a
repeat rule, read in an IANA zone. Only a one-time reminder is pinned to a UTC
instant, because FR-11 keeps it at that instant across a timezone change.
"""

import calendar
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from enum import StrEnum
from zoneinfo import ZoneInfo

# Bounds the search for the next occurrence. The longest legal gap is 99
# years (yearly, interval 99), so a few hundred candidates always suffice.
_MAX_CANDIDATES = 2_000
# A clock change moves local time by at most an hour on every zone in use; two
# hours is a safe ceiling for finding the first valid minute after a gap.
_MAX_GAP_MINUTES = 120

_WEEKDAY_SHORT = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
_WEEKDAYS_MON_TO_FRI = (0, 1, 2, 3, 4)


class RepeatKind(StrEnum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


@dataclass(frozen=True)
class ScheduleSpec:
    """One reminder's schedule. See the module docstring for the rules."""

    repeat_kind: RepeatKind
    # 1 or more. Ignored for NONE.
    repeat_interval: int
    # 0 = Monday .. 6 = Sunday. WEEKLY only, never empty there.
    repeat_weekdays: tuple[int, ...]
    # MONTHLY and YEARLY: the day asked for, 1 to 31, clamped per month (FR-8).
    repeat_month_day: int | None
    # Minute precision.
    local_time: time
    # The first occurrence's local date. Sets the phase of every interval, and
    # the month of a yearly repeat.
    anchor_local_date: date
    # NONE only: the one UTC instant this reminder fires at.
    one_time_at: datetime | None


@dataclass(frozen=True)
class ScheduleSummary:
    """FR-5's words: "Tomorrow, 7:00 PM" and "Every weekday"."""

    when_text: str
    repeat_text: str


def next_occurrence(
    *, spec: ScheduleSpec, timezone: ZoneInfo, after: datetime
) -> datetime | None:
    """The first fire instant strictly after ``after``, in UTC, or None.

    None only for a one-time reminder whose instant has passed (TC-1.12).
    """
    if spec.repeat_kind is RepeatKind.NONE:
        if spec.one_time_at is not None and spec.one_time_at > after:
            return spec.one_time_at.astimezone(UTC)
        return None

    after_local_date = after.astimezone(timezone).date()
    # Start a day early: a local date before ``after``'s can still hold an
    # instant after it when the zone is west of UTC.
    start = max(spec.anchor_local_date, after_local_date - timedelta(days=1))
    for candidate_date in _iter_candidate_dates(spec=spec, start=start):
        instant = local_to_instant(
            local_date=candidate_date, local_time=spec.local_time, timezone=timezone
        )
        if instant > after:
            return instant
    return None  # pragma: no cover — every repeating rule recurs within bounds


def local_to_instant(
    *, local_date: date, local_time: time, timezone: ZoneInfo
) -> datetime:
    """A local wall-clock minute as a UTC instant, per AD-12.

    A time that occurs twice (the clock goes back) takes its first occurrence,
    which is ``fold=0``. A time that does not exist (the clock goes forward)
    becomes the first local minute after it that does.
    """
    wall = datetime.combine(local_date, local_time, tzinfo=timezone)
    for minutes_forward in range(_MAX_GAP_MINUTES + 1):
        candidate = wall + timedelta(minutes=minutes_forward)
        if _exists_in_zone(local=candidate, timezone=timezone):
            return candidate.replace(fold=0).astimezone(UTC)
    raise ValueError("no valid local minute found after a clock change")


def describe(
    *, spec: ScheduleSpec, timezone: ZoneInfo, now: datetime
) -> ScheduleSummary:
    """FR-5: the next fire time and the repeat rule, in words."""
    next_instant = next_occurrence(spec=spec, timezone=timezone, after=now)
    shown_instant = next_instant or spec.one_time_at
    if shown_instant is None:
        when_text = "Not scheduled"
    else:
        when_text = describe_instant(instant=shown_instant, timezone=timezone, now=now)
    return ScheduleSummary(when_text=when_text, repeat_text=describe_repeat(spec=spec))


def describe_instant(*, instant: datetime, timezone: ZoneInfo, now: datetime) -> str:
    """ "Today, 7:00 PM", "Tomorrow, 9:30 AM", or "Wed 15 Oct, 9:00 AM"."""
    local = instant.astimezone(timezone)
    today = now.astimezone(timezone).date()
    clock = format_clock(clock_time=local.time())
    if local.date() == today:
        return f"Today, {clock}"
    if local.date() == today + timedelta(days=1):
        return f"Tomorrow, {clock}"
    day_label = f"{_WEEKDAY_SHORT[local.weekday()]} {local.day} {local:%b}"
    if local.year != today.year:
        day_label = f"{day_label} {local.year}"
    return f"{day_label}, {clock}"


def describe_repeat(*, spec: ScheduleSpec) -> str:
    """ "Does not repeat", "Every weekday", "Every 2 weeks on Sat", ..."""
    interval = spec.repeat_interval
    if spec.repeat_kind is RepeatKind.NONE:
        return "Does not repeat"
    if spec.repeat_kind is RepeatKind.DAILY:
        return "Every day" if interval == 1 else f"Every {interval} days"
    if spec.repeat_kind is RepeatKind.WEEKLY:
        return _describe_weekly(weekdays=spec.repeat_weekdays, interval=interval)
    month_day = spec.repeat_month_day or spec.anchor_local_date.day
    if spec.repeat_kind is RepeatKind.MONTHLY:
        unit = "month" if interval == 1 else f"{interval} months"
        return f"Every {unit} on the {_ordinal(number=month_day)}"
    unit = "year" if interval == 1 else f"{interval} years"
    return f"Every {unit} on {month_day} {spec.anchor_local_date:%b}"


def format_clock(*, clock_time: time) -> str:
    """7:00 PM. No leading zero on the hour, as the design writes it."""
    hour_12 = clock_time.hour % 12 or 12
    suffix = "AM" if clock_time.hour < 12 else "PM"
    return f"{hour_12}:{clock_time.minute:02d} {suffix}"


def clamp_to_month(*, year: int, month: int, day: int) -> date:
    """FR-8: a day the month lacks becomes the month's last day."""
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(day, last_day))


def _exists_in_zone(*, local: datetime, timezone: ZoneInfo) -> bool:
    round_trip = local.astimezone(UTC).astimezone(timezone)
    return round_trip.replace(tzinfo=None) == local.replace(tzinfo=None)


def _iter_candidate_dates(*, spec: ScheduleSpec, start: date) -> Iterator[date]:
    """Every local date the rule fires on, from ``start``, in order."""
    if spec.repeat_kind is RepeatKind.DAILY:
        yield from _iter_daily(spec=spec, start=start)
    elif spec.repeat_kind is RepeatKind.WEEKLY:
        yield from _iter_weekly(spec=spec, start=start)
    elif spec.repeat_kind is RepeatKind.MONTHLY:
        yield from _iter_monthly(spec=spec, start=start)
    else:
        yield from _iter_yearly(spec=spec, start=start)


def _iter_daily(*, spec: ScheduleSpec, start: date) -> Iterator[date]:
    interval = spec.repeat_interval
    days_since_anchor = (start - spec.anchor_local_date).days
    first_step = -(-days_since_anchor // interval)  # ceiling division
    for step in range(first_step, first_step + _MAX_CANDIDATES):
        yield spec.anchor_local_date + timedelta(days=step * interval)


def _iter_weekly(*, spec: ScheduleSpec, start: date) -> Iterator[date]:
    anchor_monday = spec.anchor_local_date - timedelta(
        days=spec.anchor_local_date.weekday()
    )
    weekdays = sorted(set(spec.repeat_weekdays))
    for day_offset in range(_MAX_CANDIDATES * 7):
        candidate = start + timedelta(days=day_offset)
        weeks_since_anchor = (candidate - anchor_monday).days // 7
        if (
            candidate >= spec.anchor_local_date
            and candidate.weekday() in weekdays
            and weeks_since_anchor % spec.repeat_interval == 0
        ):
            yield candidate


def _iter_monthly(*, spec: ScheduleSpec, start: date) -> Iterator[date]:
    anchor = spec.anchor_local_date
    month_day = spec.repeat_month_day or anchor.day
    anchor_index = anchor.year * 12 + (anchor.month - 1)
    start_index = start.year * 12 + (start.month - 1)
    months_since = max(0, start_index - anchor_index)
    first_step = -(-months_since // spec.repeat_interval)
    for step in range(max(0, first_step - 1), first_step + _MAX_CANDIDATES):
        month_index = anchor_index + step * spec.repeat_interval
        candidate = clamp_to_month(
            year=month_index // 12, month=month_index % 12 + 1, day=month_day
        )
        if candidate >= anchor and candidate >= start:
            yield candidate


def _iter_yearly(*, spec: ScheduleSpec, start: date) -> Iterator[date]:
    anchor = spec.anchor_local_date
    month_day = spec.repeat_month_day or anchor.day
    years_since = max(0, start.year - anchor.year)
    first_step = -(-years_since // spec.repeat_interval)
    for step in range(max(0, first_step - 1), first_step + _MAX_CANDIDATES):
        candidate = clamp_to_month(
            year=anchor.year + step * spec.repeat_interval,
            month=anchor.month,
            day=month_day,
        )
        if candidate >= anchor and candidate >= start:
            yield candidate


def _describe_weekly(*, weekdays: tuple[int, ...], interval: int) -> str:
    ordered = tuple(sorted(set(weekdays)))
    if interval == 1 and ordered == _WEEKDAYS_MON_TO_FRI:
        return "Every weekday"
    unit = "week" if interval == 1 else f"{interval} weeks"
    if interval == 1 and len(ordered) == 7:
        return "Every day"
    day_names = ", ".join(_WEEKDAY_SHORT[weekday] for weekday in ordered)
    return f"Every {unit} on {day_names}"


_ORDINAL_SUFFIXES = {1: "st", 2: "nd", 3: "rd"}


def _ordinal(*, number: int) -> str:
    """1st, 2nd, 3rd, 4th, 11th, 21st, 31st."""
    if 11 <= number % 100 <= 13:
        return f"{number}th"
    return f"{number}{_ORDINAL_SUFFIXES.get(number % 10, 'th')}"
