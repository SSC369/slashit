"""Firing rules that need no I/O: lateness, outage catch-up, snooze times, and
how a fired reminder's time reads. Pure; time comes in as an argument.
"""

from datetime import datetime, time, timedelta
from enum import StrEnum
from zoneinfo import ZoneInfo

from app.domains.reminders.constants import (
    MISSED_AFTER,
    ON_TIME_WINDOW,
    SNOOZE_LONG,
    SNOOZE_SHORT,
)
from app.domains.reminders.interfaces.dtos import (
    LatenessValue,
    ReminderActionValue,
    ReminderStateValue,
)
from app.domains.reminders.services.schedule import (
    ScheduleSpec,
    ScheduleSummary,
    describe,
    describe_instant,
    local_to_instant,
    next_occurrence,
)

# A year of daily occurrences: bounds the catch-up walk after a long outage.
_MAX_CATCH_UP_STEPS = 400


class SnoozeOption(StrEnum):
    """FR-21's three choices."""

    TEN_MINUTES = "ten_minutes"
    ONE_HOUR = "one_hour"
    TOMORROW = "tomorrow"


def classify_lateness(*, scheduled_for: datetime, fired_at: datetime) -> LatenessValue:
    """AD-11: on time within 5 minutes, late within 24 hours, missed after."""
    delay = fired_at - scheduled_for
    if delay <= ON_TIME_WINDOW:
        return "on_time"
    if delay <= MISSED_AFTER:
        return "late"
    return "missed"


def collapse_to_latest(
    *, spec: ScheduleSpec, timezone: ZoneInfo, scheduled_for: datetime, now: datetime
) -> datetime:
    """AD-11's one notice after an outage: of every occurrence due since
    ``scheduled_for``, only the latest one not after ``now`` fires."""
    latest = scheduled_for
    for _ in range(_MAX_CATCH_UP_STEPS):
        following = next_occurrence(spec=spec, timezone=timezone, after=latest)
        if following is None or following > now:
            return latest
        latest = following
    return latest


def snooze_instant(
    *,
    option: SnoozeOption,
    now: datetime,
    timezone: ZoneInfo,
    default_time: time,
) -> datetime:
    """FR-21: 10 minutes, 1 hour, or tomorrow at the default reminder time in
    the reminder's own zone."""
    if option is SnoozeOption.TEN_MINUTES:
        return now + SNOOZE_SHORT
    if option is SnoozeOption.ONE_HOUR:
        return now + SNOOZE_LONG
    tomorrow = now.astimezone(timezone).date() + timedelta(days=1)
    return local_to_instant(
        local_date=tomorrow, local_time=default_time, timezone=timezone
    )


def describe_fired_when(
    *,
    state: ReminderStateValue,
    last_fired_at: datetime | None,
    last_action: ReminderActionValue | None,
    timezone: ZoneInfo,
    now: datetime,
) -> str | None:
    """The Reminders tab's "Fired today, 10:00 AM" and "Missed, Sun 21 Sep,
    7:00 PM" (`Main`), or None when the reminder is not waiting on the user."""
    if state != "fired" or last_fired_at is None:
        return None
    when = describe_instant(instant=last_fired_at, timezone=timezone, now=now)
    if last_action == "missed":
        return f"Missed, {when}"
    return f"Fired {when[0].lower()}{when[1:]}"


def summarize_reminder(
    *,
    spec: ScheduleSpec,
    timezone: ZoneInfo,
    now: datetime,
    state: ReminderStateValue,
    last_fired_at: datetime | None,
    last_action: ReminderActionValue | None,
    snoozed_until: datetime | None,
) -> ScheduleSummary:
    """FR-5's words for a stored reminder: when it fired if it is waiting on
    the user, else its snooze if that comes first, else its next occurrence."""
    summary = describe(spec=spec, timezone=timezone, now=now)
    fired_text = describe_fired_when(
        state=state,
        last_fired_at=last_fired_at,
        last_action=last_action,
        timezone=timezone,
        now=now,
    )
    if fired_text is not None:
        return ScheduleSummary(when_text=fired_text, repeat_text=summary.repeat_text)
    series_next = next_occurrence(spec=spec, timezone=timezone, after=now)
    is_snooze_sooner = snoozed_until is not None and (
        series_next is None or snoozed_until < series_next
    )
    if snoozed_until is not None and is_snooze_sooner:
        return ScheduleSummary(
            when_text=describe_instant(
                instant=snoozed_until, timezone=timezone, now=now
            ),
            repeat_text=summary.repeat_text,
        )
    return summary
