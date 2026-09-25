"""Schedule maths: TC-1.1 to TC-1.12 of sub-plan 4.1. Pure, no database."""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.domains.reminders.services.schedule import (
    RepeatKind,
    ScheduleSpec,
    describe,
    local_to_instant,
    next_occurrence,
)

KOLKATA = ZoneInfo("Asia/Kolkata")
LONDON = ZoneInfo("Europe/London")
NEW_YORK = ZoneInfo("America/New_York")


def _spec(
    *,
    kind: RepeatKind,
    anchor: date,
    at: time,
    interval: int = 1,
    weekdays: tuple[int, ...] = (),
    month_day: int | None = None,
    one_time_at: datetime | None = None,
) -> ScheduleSpec:
    return ScheduleSpec(
        repeat_kind=kind,
        repeat_interval=interval,
        repeat_weekdays=weekdays,
        repeat_month_day=month_day,
        local_time=at,
        anchor_local_date=anchor,
        one_time_at=one_time_at,
    )


def _local(zone: ZoneInfo, *parts: int) -> datetime:
    year, month, day, hour, minute = parts
    return datetime(year, month, day, hour, minute, tzinfo=zone)


def test_one_time_tomorrow_evening_in_kolkata_is_the_right_instant() -> None:
    """TC-1.1."""
    fire_at = local_to_instant(
        local_date=date(2026, 9, 24), local_time=time(19, 0), timezone=KOLKATA
    )
    assert fire_at == datetime(2026, 9, 24, 13, 30, tzinfo=UTC)
    spec = _spec(
        kind=RepeatKind.NONE, anchor=date(2026, 9, 24), at=time(19), one_time_at=fire_at
    )
    now = _local(KOLKATA, 2026, 9, 23, 10, 0)
    assert next_occurrence(spec=spec, timezone=KOLKATA, after=now) == fire_at


def test_daily_seven_pm_asked_at_eight_pm_fires_tomorrow() -> None:
    """TC-1.2: the time has passed today, so the next occurrence is tomorrow."""
    spec = _spec(kind=RepeatKind.DAILY, anchor=date(2026, 9, 23), at=time(19))
    now = _local(KOLKATA, 2026, 9, 23, 20, 0)
    fire_at = next_occurrence(spec=spec, timezone=KOLKATA, after=now)
    assert fire_at is not None
    assert fire_at.astimezone(KOLKATA) == _local(KOLKATA, 2026, 9, 24, 19, 0)


def test_weekdays_asked_on_friday_evening_fire_next_monday() -> None:
    """TC-1.3. 2026-09-25 is a Friday."""
    spec = _spec(
        kind=RepeatKind.WEEKLY,
        anchor=date(2026, 9, 21),
        at=time(9, 30),
        weekdays=(0, 1, 2, 3, 4),
    )
    now = _local(KOLKATA, 2026, 9, 25, 18, 0)
    fire_at = next_occurrence(spec=spec, timezone=KOLKATA, after=now)
    assert fire_at is not None
    assert fire_at.astimezone(KOLKATA) == _local(KOLKATA, 2026, 9, 28, 9, 30)


def test_every_two_weeks_on_saturday_skips_the_week_between() -> None:
    """TC-1.4. Anchor Saturday 2026-09-26; the next is 10 October, not 3rd."""
    spec = _spec(
        kind=RepeatKind.WEEKLY,
        anchor=date(2026, 9, 26),
        at=time(8),
        interval=2,
        weekdays=(5,),
    )
    after_first = _local(KOLKATA, 2026, 9, 26, 9, 0)
    fire_at = next_occurrence(spec=spec, timezone=KOLKATA, after=after_first)
    assert fire_at is not None
    assert fire_at.astimezone(KOLKATA).date() == date(2026, 10, 10)


def test_monthly_on_the_31st_clamps_to_30_september_then_31_october() -> None:
    """TC-1.5, FR-8."""
    spec = _spec(
        kind=RepeatKind.MONTHLY, anchor=date(2026, 9, 30), at=time(9), month_day=31
    )
    now = _local(KOLKATA, 2026, 9, 23, 10, 0)
    first = next_occurrence(spec=spec, timezone=KOLKATA, after=now)
    assert first is not None
    assert first.astimezone(KOLKATA).date() == date(2026, 9, 30)
    second = next_occurrence(spec=spec, timezone=KOLKATA, after=first)
    assert second is not None
    assert second.astimezone(KOLKATA).date() == date(2026, 10, 31)


def test_yearly_on_29_february_fires_on_28_february_in_2027() -> None:
    """TC-1.6, FR-8."""
    spec = _spec(
        kind=RepeatKind.YEARLY, anchor=date(2027, 2, 28), at=time(9), month_day=29
    )
    now = _local(KOLKATA, 2026, 9, 23, 10, 0)
    first = next_occurrence(spec=spec, timezone=KOLKATA, after=now)
    assert first is not None
    assert first.astimezone(KOLKATA).date() == date(2027, 2, 28)
    leap = next_occurrence(
        spec=spec, timezone=KOLKATA, after=_local(KOLKATA, 2028, 1, 1, 0, 0)
    )
    assert leap is not None
    assert leap.astimezone(KOLKATA).date() == date(2028, 2, 29)


def test_daily_seven_am_in_london_stays_seven_across_the_october_change() -> None:
    """TC-1.7, FR-9. British clocks go back on 2026-10-25."""
    spec = _spec(kind=RepeatKind.DAILY, anchor=date(2026, 10, 20), at=time(7))
    # The change is at 01:00 UTC on the 25th, so 07:00 that day is already GMT.
    before = next_occurrence(
        spec=spec, timezone=LONDON, after=_local(LONDON, 2026, 10, 23, 8, 0)
    )
    after = next_occurrence(
        spec=spec, timezone=LONDON, after=_local(LONDON, 2026, 10, 24, 8, 0)
    )
    assert before is not None and after is not None
    assert before.astimezone(LONDON).hour == 7
    assert after.astimezone(LONDON).hour == 7
    assert before == datetime(2026, 10, 24, 6, 0, tzinfo=UTC)  # 07:00 BST
    assert after == datetime(2026, 10, 25, 7, 0, tzinfo=UTC)  # 07:00 GMT


def test_a_time_skipped_by_spring_forward_fires_at_the_first_valid_minute() -> None:
    """TC-1.8, AD-12. New York skips 02:00 to 03:00 on 2026-03-08."""
    fire_at = local_to_instant(
        local_date=date(2026, 3, 8), local_time=time(2, 30), timezone=NEW_YORK
    )
    assert fire_at.astimezone(NEW_YORK).replace(tzinfo=None) == datetime(
        2026, 3, 8, 3, 0
    )


def test_a_time_repeated_by_fall_back_fires_once_at_the_first() -> None:
    """TC-1.9, AD-12. New York repeats 01:00 to 02:00 on 2026-11-01."""
    spec = _spec(kind=RepeatKind.DAILY, anchor=date(2026, 10, 30), at=time(1, 30))
    first = next_occurrence(
        spec=spec, timezone=NEW_YORK, after=_local(NEW_YORK, 2026, 10, 31, 12, 0)
    )
    assert first == datetime(2026, 11, 1, 5, 30, tzinfo=UTC)  # 01:30 EDT
    following = next_occurrence(spec=spec, timezone=NEW_YORK, after=first)
    assert following is not None
    assert following.astimezone(NEW_YORK).date() == date(2026, 11, 2)


def test_describe_reads_the_time_and_the_repeat_in_words() -> None:
    """TC-1.10, FR-5."""
    spec = _spec(
        kind=RepeatKind.WEEKLY,
        anchor=date(2026, 9, 24),
        at=time(19),
        weekdays=(0, 1, 2, 3, 4),
    )
    summary = describe(
        spec=spec, timezone=KOLKATA, now=_local(KOLKATA, 2026, 9, 23, 20, 0)
    )
    assert summary.when_text == "Tomorrow, 7:00 PM"
    assert summary.repeat_text == "Every weekday"


def test_describe_names_other_repeats_and_far_dates() -> None:
    """TC-1.10, the remaining phrasings the design draws."""
    monthly = _spec(
        kind=RepeatKind.MONTHLY, anchor=date(2026, 9, 30), at=time(9), month_day=31
    )
    fortnightly = _spec(
        kind=RepeatKind.WEEKLY,
        anchor=date(2026, 9, 26),
        at=time(8),
        interval=2,
        weekdays=(5,),
    )
    now = _local(KOLKATA, 2026, 9, 23, 10, 0)
    assert describe(spec=monthly, timezone=KOLKATA, now=now).repeat_text == (
        "Every month on the 31st"
    )
    assert describe(spec=monthly, timezone=KOLKATA, now=now).when_text == (
        "Wed 30 Sep, 9:00 AM"
    )
    assert describe(spec=fortnightly, timezone=KOLKATA, now=now).repeat_text == (
        "Every 2 weeks on Sat"
    )


def test_a_date_with_the_default_time_resolves_to_that_minute() -> None:
    """TC-1.11, FR-3: the interactor supplies the default time; the maths
    treats it like any other time."""
    default_time = time(9, 0)
    fire_at = local_to_instant(
        local_date=date(2026, 10, 15), local_time=default_time, timezone=KOLKATA
    )
    assert fire_at.astimezone(KOLKATA) == _local(KOLKATA, 2026, 10, 15, 9, 0)


def test_a_passed_one_time_instant_never_comes_back() -> None:
    """TC-1.12."""
    passed = datetime(2026, 9, 23, 1, 0, tzinfo=UTC)
    spec = _spec(
        kind=RepeatKind.NONE,
        anchor=date(2026, 9, 23),
        at=time(6, 30),
        one_time_at=passed,
    )
    assert (
        next_occurrence(
            spec=spec, timezone=KOLKATA, after=passed + timedelta(minutes=1)
        )
        is None
    )
