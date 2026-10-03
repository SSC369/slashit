"""Epic 007, sub-plan 4.1 §7: the date rules of `events.services.schedule`."""

import random
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.domains.events.services.schedule import (
    AlertTime,
    EventStatus,
    LocalSchedule,
    NormalisedLeads,
    SaidSchedule,
    alert_fire_times,
    alert_fires_at,
    describe_alert,
    describe_when,
    event_status,
    normalise_leads,
    normalise_said_schedule,
    resolve,
)

KOLKATA = "Asia/Kolkata"
TODAY = date(2026, 10, 2)
NOW = datetime(2026, 10, 2, 10, 0, tzinfo=ZoneInfo(KOLKATA)).astimezone(UTC)

# Twelve zones, including both sides of the date line (NFR-3).
ZONES = (
    "Pacific/Kiritimati",
    "Pacific/Pago_Pago",
    "Pacific/Auckland",
    "Asia/Kolkata",
    "Asia/Kathmandu",
    "Europe/London",
    "Europe/Berlin",
    "America/New_York",
    "America/Los_Angeles",
    "America/St_Johns",
    "Australia/Adelaide",
    "UTC",
)


def _said(
    *,
    start_date: date,
    has_year: bool = False,
    start_time: time | None = None,
    end_date: date | None = None,
    end_time: time | None = None,
    repeat_yearly: bool = False,
) -> SaidSchedule:
    return SaidSchedule(
        start_date=start_date,
        has_year=has_year,
        start_time=start_time,
        end_date=end_date,
        end_time=end_time,
        repeat_yearly=repeat_yearly,
    )


def _schedule(
    *,
    start_date: date,
    start_time: time | None = None,
    end_date: date | None = None,
    end_time: time | None = None,
    repeat_yearly: bool = False,
    timezone: str = KOLKATA,
) -> LocalSchedule:
    return LocalSchedule(
        start_date=start_date,
        start_time=start_time,
        end_date=end_date,
        end_time=end_time,
        repeat_yearly=repeat_yearly,
        timezone=timezone,
    )


def test_a_passed_date_with_no_year_moves_to_next_year() -> None:
    """FR-4."""
    normalised = normalise_said_schedule(
        said=_said(start_date=date(2026, 10, 1)), local_today=TODAY
    )
    assert normalised.start_date == date(2027, 10, 1)
    assert "1 Oct has passed this year, so next year" in normalised.notes


def test_today_with_no_year_stays_today() -> None:
    normalised = normalise_said_schedule(
        said=_said(start_date=TODAY), local_today=TODAY
    )
    assert normalised.start_date == TODAY


def test_a_stated_past_year_is_kept_and_reads_as_past() -> None:
    """FR-5."""
    normalised = normalise_said_schedule(
        said=_said(start_date=date(2019, 6, 14), has_year=True), local_today=TODAY
    )
    assert normalised.start_date == date(2019, 6, 14)
    assert "A past date, saved as given" in normalised.notes
    resolved = resolve(schedule=_schedule(start_date=date(2019, 6, 14)), now=NOW)
    assert event_status(resolved=resolved, now=NOW) == EventStatus.PAST


def test_no_time_is_all_day() -> None:
    """FR-3."""
    normalised = normalise_said_schedule(
        said=_said(start_date=date(2026, 10, 12), end_time=time(17)), local_today=TODAY
    )
    assert normalised.start_time is None
    assert normalised.end_time is None
    assert "No time given, so all day" in normalised.notes


def test_an_end_time_before_the_start_ends_the_next_day() -> None:
    """FR-7."""
    normalised = normalise_said_schedule(
        said=_said(start_date=date(2026, 10, 3), start_time=time(23), end_time=time(1)),
        local_today=TODAY,
    )
    assert normalised.end_date == date(2026, 10, 4)
    assert "Ends after midnight, so on Sun 4 Oct" in normalised.notes


def test_a_range_across_new_year_ends_the_following_year() -> None:
    normalised = normalise_said_schedule(
        said=_said(start_date=date(2026, 12, 28), end_date=date(2026, 1, 2)),
        local_today=TODAY,
    )
    assert normalised.end_date == date(2027, 1, 2)


def test_a_multi_day_event_is_listed_until_its_last_day_ends() -> None:
    """FR-6, FR-24."""
    schedule = _schedule(start_date=date(2026, 12, 20), end_date=date(2026, 12, 24))
    resolved = resolve(schedule=schedule, now=NOW)
    last_evening = datetime(2026, 12, 24, 23, 0, tzinfo=ZoneInfo(KOLKATA))
    assert (
        event_status(resolved=resolved, now=last_evening) == EventStatus.HAPPENING_NOW
    )
    assert event_status(resolved=resolved, now=last_evening + timedelta(hours=2)) == (
        EventStatus.PAST
    )
    assert (
        describe_when(schedule=schedule, resolved=resolved, local_today=TODAY)
        == "Sun 20 to Thu 24 Dec, all day"
    )


def test_a_yearly_february_29_falls_on_the_28th_in_a_common_year() -> None:
    """FR-10."""
    schedule = _schedule(start_date=date(2028, 2, 29), repeat_yearly=True)
    in_2027 = datetime(2027, 1, 1, tzinfo=UTC)
    assert resolve(schedule=schedule, now=in_2027).occurrence_date == date(2028, 2, 29)
    leap_anchor = _schedule(start_date=date(2024, 2, 29), repeat_yearly=True)
    assert resolve(schedule=leap_anchor, now=in_2027).occurrence_date == date(
        2027, 2, 28
    )
    in_2028 = datetime(2028, 1, 1, tzinfo=UTC)
    assert resolve(schedule=leap_anchor, now=in_2028).occurrence_date == date(
        2028, 2, 29
    )


def test_a_yearly_event_resolves_to_its_next_occurrence() -> None:
    schedule = _schedule(start_date=date(1960, 10, 12), repeat_yearly=True)
    assert resolve(schedule=schedule, now=NOW).occurrence_date == date(2026, 10, 12)
    after = datetime(2026, 10, 13, 12, tzinfo=UTC)
    assert resolve(schedule=schedule, now=after).occurrence_date == date(2027, 10, 12)


def test_a_timed_event_with_no_end_stays_listed_until_local_midnight() -> None:
    """FR-25."""
    schedule = _schedule(start_date=TODAY, start_time=time(9))
    resolved = resolve(schedule=schedule, now=NOW)
    evening = datetime(2026, 10, 2, 23, 30, tzinfo=ZoneInfo(KOLKATA))
    assert event_status(resolved=resolved, now=evening) == EventStatus.HAPPENING_NOW
    assert event_status(resolved=resolved, now=evening + timedelta(hours=1)) == (
        EventStatus.PAST
    )


def test_status_is_upcoming_then_happening_then_past() -> None:
    """Design Q3."""
    schedule = _schedule(start_date=TODAY, start_time=time(14), end_time=time(17))
    resolved = resolve(schedule=schedule, now=NOW)
    zone = ZoneInfo(KOLKATA)
    assert event_status(resolved=resolved, now=NOW) == EventStatus.UPCOMING
    during = datetime(2026, 10, 2, 15, tzinfo=zone)
    assert event_status(resolved=resolved, now=during) == EventStatus.HAPPENING_NOW
    after = datetime(2026, 10, 2, 18, tzinfo=zone)
    assert event_status(resolved=resolved, now=after) == EventStatus.PAST


def test_when_text_matches_the_design() -> None:
    timed = _schedule(
        start_date=date(2026, 10, 9), start_time=time(16), end_time=time(17)
    )
    assert (
        describe_when(
            schedule=timed, resolved=resolve(schedule=timed, now=NOW), local_today=TODAY
        )
        == "Fri 9 Oct, 4:00 to 5:00 PM"
    )
    overnight = _schedule(
        start_date=date(2026, 10, 3),
        start_time=time(23),
        end_date=date(2026, 10, 4),
        end_time=time(1),
    )
    assert (
        describe_when(
            schedule=overnight,
            resolved=resolve(schedule=overnight, now=NOW),
            local_today=TODAY,
        )
        == "Tomorrow, 11:00 PM to 1:00 AM"
    )
    next_year = _schedule(start_date=date(2027, 10, 1))
    assert (
        describe_when(
            schedule=next_year,
            resolved=resolve(schedule=next_year, now=NOW),
            local_today=TODAY,
        )
        == "Fri 1 Oct 2027, all day"
    )


def test_alert_words() -> None:
    assert describe_alert(lead_minutes=0) == "At start"
    assert describe_alert(lead_minutes=1440) == "1 day before"
    assert describe_alert(lead_minutes=10080) == "1 week before"
    assert describe_alert(lead_minutes=120) == "2 hours before"
    assert describe_alert(lead_minutes=15) == "15 minutes before"


def test_an_all_day_alert_counts_back_from_the_default_reminder_time() -> None:
    """FR-15."""
    schedule = _schedule(start_date=date(2026, 10, 12))
    fires_at = alert_fires_at(
        schedule=schedule,
        resolved=resolve(schedule=schedule, now=NOW),
        lead_minutes=1440,
        default_reminder_time=time(9),
    )
    assert fires_at == datetime(2026, 10, 11, 9, tzinfo=ZoneInfo(KOLKATA))


def test_a_timed_alert_counts_back_from_the_start() -> None:
    """FR-14."""
    schedule = _schedule(start_date=date(2026, 10, 9), start_time=time(16))
    fires_at = alert_fires_at(
        schedule=schedule,
        resolved=resolve(schedule=schedule, now=NOW),
        lead_minutes=60,
        default_reminder_time=time(9),
    )
    assert fires_at == datetime(2026, 10, 9, 15, tzinfo=ZoneInfo(KOLKATA))


def test_leads_are_kept_once_shortest_first() -> None:
    """Epic 007, 4.2 C-2: FR-14 and FR-34."""
    assert normalise_leads(leads=[1440, 120, 1440]) == NormalisedLeads(
        leads=(120, 1440), had_repeat=True
    )
    assert normalise_leads(leads=[10080, 1440]) == NormalisedLeads(
        leads=(1440, 10080), had_repeat=False
    )
    assert normalise_leads(leads=[]) == NormalisedLeads(leads=(), had_repeat=False)


def test_a_lead_out_of_range_is_not_said_and_is_no_repeat() -> None:
    """A lead below zero or over a year is dropped, as slice 1 did."""
    assert normalise_leads(leads=[-5, 0, 525601, 525601]) == NormalisedLeads(
        leads=(0,), had_repeat=False
    )


def test_each_lead_fires_soonest_first_on_an_all_day_event() -> None:
    """4.2 C-3: FR-15 for every lead, in the order the cap sets them."""
    schedule = _schedule(start_date=date(2026, 11, 21))
    alert_times = alert_fire_times(
        schedule=schedule,
        resolved=resolve(schedule=schedule, now=NOW),
        leads=(1440, 10080),
        default_reminder_time=time(9),
    )
    assert alert_times == (
        AlertTime(
            lead_minutes=10080,
            fires_at=datetime(2026, 11, 14, 9, tzinfo=ZoneInfo(KOLKATA)),
        ),
        AlertTime(
            lead_minutes=1440,
            fires_at=datetime(2026, 11, 20, 9, tzinfo=ZoneInfo(KOLKATA)),
        ),
    )


def test_each_lead_fires_soonest_first_on_a_timed_event() -> None:
    """4.2 C-1: "remind me 1 day before and 1 hour before" on a 4 PM event."""
    schedule = _schedule(start_date=date(2026, 10, 9), start_time=time(16))
    alert_times = alert_fire_times(
        schedule=schedule,
        resolved=resolve(schedule=schedule, now=NOW),
        leads=(60, 1440),
        default_reminder_time=time(9),
    )
    assert [alert_time.fires_at for alert_time in alert_times] == [
        datetime(2026, 10, 8, 16, tzinfo=ZoneInfo(KOLKATA)),
        datetime(2026, 10, 9, 15, tzinfo=ZoneInfo(KOLKATA)),
    ]
    assert (
        alert_fire_times(
            schedule=schedule,
            resolved=resolve(schedule=schedule, now=NOW),
            leads=(),
            default_reminder_time=time(9),
        )
        == ()
    )


def test_resolved_instants_hold_their_shape_over_random_schedules() -> None:
    """Index §8: starts_at <= ends_at, and an all-day event's local dates
    round-trip in every zone, so it never moves a day (FR-12, NFR-3)."""
    rng = random.Random(7)
    for _ in range(1000):
        zone_name = rng.choice(ZONES)
        start_date = date(2026, 1, 1) + timedelta(days=rng.randrange(730))
        all_day = rng.random() < 0.5
        start_time = None if all_day else time(rng.randrange(24), rng.choice((0, 30)))
        span = rng.choice((0, 0, 1, 3))
        end_date = start_date + timedelta(days=span) if span else None
        end_time = None if all_day or rng.random() < 0.5 else time(rng.randrange(24), 0)
        schedule = _schedule(
            start_date=start_date,
            start_time=start_time,
            end_date=end_date,
            end_time=end_time,
            repeat_yearly=rng.random() < 0.3,
            timezone=zone_name,
        )
        resolved = resolve(schedule=schedule, now=NOW)
        assert resolved.starts_at <= resolved.ends_at
        if all_day:
            zone = ZoneInfo(zone_name)
            assert (
                resolved.starts_at.astimezone(zone).date() == resolved.occurrence_date
            )
            assert resolved.starts_at.astimezone(zone).time() == time(0)
