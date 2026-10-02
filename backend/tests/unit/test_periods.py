"""Epic 006, sub-plan 4.2 §7: C-22 to C-26. Reading summary periods by code."""

from datetime import date

import pytest

from app.domains.expenses.interfaces.dtos import Period, PeriodKey
from app.domains.expenses.services.periods import parse_period, picker_periods

# Friday, as the design's artboards are drawn.
TODAY = date(2026, 10, 2)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "today",
            Period(
                PeriodKey.TODAY, date(2026, 10, 2), date(2026, 10, 2), "Today", "today"
            ),
        ),
        (
            "this week",
            Period(
                PeriodKey.THIS_WEEK,
                date(2026, 9, 28),
                date(2026, 10, 4),
                "This week",
                "this week",
            ),
        ),
        (
            "last week",
            Period(
                PeriodKey.LAST_WEEK,
                date(2026, 9, 21),
                date(2026, 9, 27),
                "Last week",
                "last week",
            ),
        ),
        (
            "this month",
            Period(
                PeriodKey.THIS_MONTH,
                date(2026, 10, 1),
                date(2026, 10, 31),
                "October 2026 so far",
                "this month",
            ),
        ),
        (
            "last month",
            Period(
                PeriodKey.LAST_MONTH,
                date(2026, 9, 1),
                date(2026, 9, 30),
                "September 2026",
                "in September 2026",
            ),
        ),
        (
            "august",
            Period(
                PeriodKey.MONTH,
                date(2026, 8, 1),
                date(2026, 8, 31),
                "August 2026",
                "in August 2026",
            ),
        ),
        (
            "this year",
            Period(
                PeriodKey.THIS_YEAR,
                date(2026, 1, 1),
                date(2026, 12, 31),
                "2026 so far",
                "this year",
            ),
        ),
    ],
)
def test_each_period_on_the_list_reads_to_its_range_label_and_phrase(
    text: str, expected: Period
) -> None:
    """C-22."""
    assert parse_period(text=text, today=TODAY) == expected


def test_no_period_and_this_months_own_name_read_as_this_month() -> None:
    """C-23, FR-24."""
    this_month = parse_period(text="this month", today=TODAY)
    assert parse_period(text="", today=TODAY) == this_month
    assert parse_period(text="   ", today=TODAY) == this_month
    assert parse_period(text="october", today=TODAY) == this_month


@pytest.mark.parametrize(
    ("text", "start"),
    [
        ("november", date(2025, 11, 1)),
        ("Aug", date(2026, 8, 1)),
        ("SEPT", date(2026, 9, 1)),
        ("  last   month ", date(2026, 9, 1)),
        ("January", date(2026, 1, 1)),
    ],
)
def test_a_month_without_a_year_is_the_most_recent_not_after_today(
    text: str, start: date
) -> None:
    """C-23."""
    period = parse_period(text=text, today=TODAY)
    assert period is not None
    assert period.start == start


@pytest.mark.parametrize(
    "text", ["since diwali", "last 7 days", "2025", "august 2025", "yesterday"]
)
def test_anything_off_the_list_is_not_understood(text: str) -> None:
    """C-24, FR-27."""
    assert parse_period(text=text, today=TODAY) is None


def test_periods_cross_the_year_end() -> None:
    """C-25. Monday 5 January 2026."""
    today = date(2026, 1, 5)
    last_week = parse_period(text="last week", today=today)
    last_month = parse_period(text="last month", today=today)
    december = parse_period(text="december", today=today)
    assert last_week is not None and last_month is not None
    assert (last_week.start, last_week.end) == (date(2025, 12, 29), date(2026, 1, 4))
    assert (last_month.start, last_month.end) == (date(2025, 12, 1), date(2025, 12, 31))
    assert december == Period(
        PeriodKey.MONTH,
        date(2025, 12, 1),
        date(2025, 12, 31),
        "December 2025",
        "in December 2025",
    )


def test_february_ends_on_its_last_day() -> None:
    period = parse_period(text="february", today=date(2028, 3, 10))
    assert period is not None
    assert period.end == date(2028, 2, 29)


def test_the_picker_lists_nineteen_periods_ending_with_all_time() -> None:
    """C-26, decisions 2A and 4A."""
    periods = picker_periods(today=TODAY)

    assert [period.label for period in periods] == [
        "Today",
        "This week",
        "Last week",
        "October 2026 so far",
        "September 2026",
        "August 2026",
        "July 2026",
        "June 2026",
        "May 2026",
        "April 2026",
        "March 2026",
        "February 2026",
        "January 2026",
        "December 2025",
        "November 2025",
        "October 2025",
        "September 2025",
        "2026 so far",
        "All time",
    ]
    assert (periods[-1].start, periods[-1].end) == (None, None)


def test_the_picker_and_typed_text_resolve_to_the_same_range() -> None:
    """FR-28 by construction."""
    by_label = {period.label: period for period in picker_periods(today=TODAY)}
    for text in (
        "today",
        "this week",
        "last week",
        "this month",
        "last month",
        "march",
    ):
        typed = parse_period(text=text, today=TODAY)
        assert typed is not None
        assert by_label[typed.label] == typed
