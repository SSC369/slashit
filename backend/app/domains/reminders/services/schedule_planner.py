"""Turns what a sentence said into a schedule. Pure: time comes in as an argument.

The rules the PRD sets for incomplete input live here, once, for both a
``/remind`` capture and an answered question:

- No time given: the user's default reminder time (FR-3).
- A one-time reminder at a time already passed today: tomorrow (FR-4).
- No date where the rule needs one to start from: ask (FR-2). Daily and
  weekly start today without one; one-time, monthly and yearly cannot.
- A monthly or yearly day the month lacks: clamped by the schedule (FR-8).

Each rule that changed what was said is named back in ``when_note``, so the
confirmation card can explain the time it shows (design, ``RemindResolved``).
"""

import calendar
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.domains.reminders.interfaces.dtos import ReminderFields, UserClockDTO
from app.domains.reminders.services.schedule import (
    RepeatKind,
    ScheduleSpec,
    clamp_to_month,
    format_clock,
    local_to_instant,
    next_occurrence,
)


@dataclass(frozen=True)
class PlannedSchedule:
    spec: ScheduleSpec
    next_fire_at: datetime | None
    when_note: str | None


def plan_schedule(
    *, fields: ReminderFields, clock: UserClockDTO, now: datetime
) -> PlannedSchedule | None:
    """The schedule the fields describe, or None when a date must be asked for."""
    timezone = ZoneInfo(clock.timezone)
    today = now.astimezone(timezone).date()
    local_time = fields.local_time or clock.default_reminder_time
    if fields.repeat_kind is RepeatKind.NONE:
        spec = _one_time_spec(
            local_date=fields.local_date,
            local_time=local_time,
            today=today,
            timezone=timezone,
            now=now,
        )
    else:
        spec = _repeating_spec(fields=fields, local_time=local_time, today=today)
    if spec is None:
        return None
    next_fire_at = next_occurrence(spec=spec, timezone=timezone, after=now)
    return PlannedSchedule(
        spec=spec,
        next_fire_at=next_fire_at,
        when_note=_explain_resolved_time(
            fields=fields,
            spec=spec,
            next_local_date=(
                next_fire_at.astimezone(timezone).date() if next_fire_at else None
            ),
        ),
    )


def _explain_resolved_time(
    *, fields: ReminderFields, spec: ScheduleSpec, next_local_date: date | None
) -> str | None:
    """The one rule that most changed what was said, in the design's words.
    A moved day outranks a filled-in time, since it is the bigger surprise."""
    was_moved_past_today = (
        spec.repeat_kind is RepeatKind.NONE
        and fields.local_date is not None
        and spec.anchor_local_date != fields.local_date
    )
    if was_moved_past_today:
        return f"{format_clock(clock_time=spec.local_time)} has already passed today"
    month_day = spec.repeat_month_day
    if month_day is not None and next_local_date is not None:
        days_in_month = calendar.monthrange(
            next_local_date.year, next_local_date.month
        )[1]
        if month_day > days_in_month:
            month_name = f"{next_local_date:%B}"
            return f"{month_name} has {days_in_month} days, so the last day"
    if fields.local_time is None:
        return "No time given, so your default reminder time"
    return None


def _one_time_spec(
    *,
    local_date: date | None,
    local_time: time,
    today: date,
    timezone: ZoneInfo,
    now: datetime,
) -> ScheduleSpec | None:
    if local_date is None or local_date < today:
        return None
    instant = local_to_instant(
        local_date=local_date, local_time=local_time, timezone=timezone
    )
    if instant <= now:
        local_date = local_date + timedelta(days=1)
        instant = local_to_instant(
            local_date=local_date, local_time=local_time, timezone=timezone
        )
    return ScheduleSpec(
        repeat_kind=RepeatKind.NONE,
        repeat_interval=1,
        repeat_weekdays=(),
        repeat_month_day=None,
        local_time=local_time,
        anchor_local_date=local_date,
        one_time_at=instant,
    )


def _repeating_spec(
    *, fields: ReminderFields, local_time: time, today: date
) -> ScheduleSpec | None:
    kind = fields.repeat_kind
    month_day = _month_day(fields=fields)
    anchor = _repeating_anchor(fields=fields, month_day=month_day, today=today)
    if anchor is None:
        return None
    weekdays: tuple[int, ...] = ()
    if kind is RepeatKind.WEEKLY:
        weekdays = tuple(sorted(set(fields.repeat_weekdays))) or (anchor.weekday(),)
    return ScheduleSpec(
        repeat_kind=kind,
        repeat_interval=fields.repeat_interval,
        repeat_weekdays=weekdays,
        repeat_month_day=month_day,
        local_time=local_time,
        anchor_local_date=anchor,
        one_time_at=None,
    )


def _month_day(*, fields: ReminderFields) -> int | None:
    if fields.repeat_kind not in (RepeatKind.MONTHLY, RepeatKind.YEARLY):
        return None
    if fields.month_day is not None:
        return fields.month_day
    return fields.local_date.day if fields.local_date is not None else None


def _repeating_anchor(
    *, fields: ReminderFields, month_day: int | None, today: date
) -> date | None:
    kind = fields.repeat_kind
    if kind in (RepeatKind.DAILY, RepeatKind.WEEKLY):
        return fields.local_date or today
    if kind is RepeatKind.MONTHLY:
        if month_day is None:
            return None
        return _first_monthly_date(
            base=fields.local_date or today, day=month_day, today=today
        )
    if fields.local_date is None or month_day is None:
        return None
    return _first_yearly_date(month=fields.local_date.month, day=month_day, today=today)


def _first_monthly_date(*, base: date, day: int, today: date) -> date:
    candidate = clamp_to_month(year=base.year, month=base.month, day=day)
    if candidate >= today:
        return candidate
    following = base.replace(day=1) + timedelta(days=32)
    return clamp_to_month(year=following.year, month=following.month, day=day)


def _first_yearly_date(*, month: int, day: int, today: date) -> date:
    candidate = clamp_to_month(year=today.year, month=month, day=day)
    if candidate >= today:
        return candidate
    return clamp_to_month(year=today.year + 1, month=month, day=day)
