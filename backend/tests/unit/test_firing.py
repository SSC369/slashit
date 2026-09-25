"""Pure firing rules: TC-2.1, TC-2.2, TC-2.8, and the fired wording."""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.domains.reminders.interfaces.dtos import LatenessValue
from app.domains.reminders.services.firing import (
    SnoozeOption,
    classify_lateness,
    collapse_to_latest,
    describe_fired_when,
    snooze_instant,
)
from app.domains.reminders.services.schedule import RepeatKind, ScheduleSpec

KOLKATA = ZoneInfo("Asia/Kolkata")
SET_TIME = datetime(2026, 9, 23, 13, 30, tzinfo=UTC)  # 19:00 in Kolkata


@pytest.mark.parametrize(
    ("delay", "expected"),
    [
        (timedelta(minutes=5), "on_time"),
        (timedelta(minutes=5, seconds=1), "late"),
        (timedelta(hours=24), "late"),
        (timedelta(hours=24, seconds=1), "missed"),
    ],
)
def test_lateness_boundaries(delay: timedelta, expected: LatenessValue) -> None:
    """TC-2.1, AD-11."""
    assert (
        classify_lateness(scheduled_for=SET_TIME, fired_at=SET_TIME + delay) == expected
    )


def test_a_three_day_outage_collapses_to_the_latest_occurrence() -> None:
    """TC-2.2: one notice, for the latest occurrence, not three."""
    daily = ScheduleSpec(
        repeat_kind=RepeatKind.DAILY,
        repeat_interval=1,
        repeat_weekdays=(),
        repeat_month_day=None,
        local_time=time(19),
        anchor_local_date=date(2026, 9, 20),
        one_time_at=None,
    )
    first_missed = datetime(2026, 9, 20, 13, 30, tzinfo=UTC)
    now = datetime(2026, 9, 23, 14, 0, tzinfo=UTC)

    latest = collapse_to_latest(
        spec=daily, timezone=KOLKATA, scheduled_for=first_missed, now=now
    )

    assert latest == SET_TIME
    assert classify_lateness(scheduled_for=latest, fired_at=now) == "late"


@pytest.mark.parametrize(
    ("option", "expected"),
    [
        (SnoozeOption.TEN_MINUTES, SET_TIME + timedelta(minutes=10)),
        (SnoozeOption.ONE_HOUR, SET_TIME + timedelta(hours=1)),
        # Tomorrow, 24 September, at 09:00 Kolkata.
        (SnoozeOption.TOMORROW, datetime(2026, 9, 24, 3, 30, tzinfo=UTC)),
    ],
)
def test_snooze_instants(option: SnoozeOption, expected: datetime) -> None:
    """TC-2.8, FR-21."""
    assert (
        snooze_instant(
            option=option, now=SET_TIME, timezone=KOLKATA, default_time=time(9)
        )
        == expected
    )


def test_fired_and_missed_read_as_the_design_writes_them() -> None:
    now = SET_TIME + timedelta(minutes=30)
    assert (
        describe_fired_when(
            state="fired",
            last_fired_at=SET_TIME,
            last_action=None,
            timezone=KOLKATA,
            now=now,
        )
        == "Fired today, 7:00 PM"
    )
    assert (
        describe_fired_when(
            state="fired",
            last_fired_at=SET_TIME - timedelta(days=2),
            last_action="missed",
            timezone=KOLKATA,
            now=now,
        )
        == "Missed, Mon 21 Sep, 7:00 PM"
    )
    assert (
        describe_fired_when(
            state="upcoming",
            last_fired_at=SET_TIME,
            last_action=None,
            timezone=KOLKATA,
            now=now,
        )
        is None
    )
