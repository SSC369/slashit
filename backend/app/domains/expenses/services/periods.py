"""Periods for expense summaries, sub-plan 4.2 §5.

FR-23's list is closed, so code reads it exactly (build plan AD-5). The same
functions resolve a typed ``/expenses`` period and the Records picker's
options, so both give one ``{start, end}`` range and FR-28 holds by
construction. Pure: today is passed in, in the user's zone (AD-3).
"""

import calendar
import re
from collections.abc import Callable
from datetime import date, timedelta

from app.domains.expenses.interfaces.dtos import Period, PeriodKey

# Decision 4A: the named months before last month in the picker.
PICKER_NAMED_MONTHS = 12

# Spelled out rather than read from ``calendar``, whose names follow the
# process locale.
_MONTH_NAMES = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
_MONTH_WORDS: dict[str, int] = {"sept": 9}
for _number, _name in enumerate(_MONTH_NAMES, start=1):
    _MONTH_WORDS[_name.lower()] = _number
    _MONTH_WORDS[_name[:3].lower()] = _number


def parse_period(*, text: str, today: date) -> Period | None:
    """FR-23 and FR-24. Empty text is this month; anything off the list is
    None, which capture refuses (FR-27)."""
    words = re.sub(r"\s+", " ", text.strip().lower())
    fixed = _FIXED_PERIODS.get(words)
    if fixed is not None:
        return fixed(today)
    month = _MONTH_WORDS.get(words)
    if month is not None:
        return _most_recent_month(month=month, today=today)
    return None


def picker_periods(*, today: date) -> list[Period]:
    """The Records picker, decisions 2A and 4A: the fixed periods, the 12
    months before last month by name, newest first, then This year and All
    time."""
    periods = [
        _FIXED_PERIODS[words](today)
        for words in ("today", "this week", "last week", "this month", "last month")
    ]
    first = _month_before(first=today.replace(day=1))
    for _ in range(PICKER_NAMED_MONTHS):
        first = _month_before(first=first)
        periods.append(_named_month(first=first, key=PeriodKey.MONTH))
    periods.append(_this_year(today))
    periods.append(
        Period(
            key=PeriodKey.ALL_TIME, start=None, end=None, label="All time", phrase="yet"
        )
    )
    return periods


def _today(today: date) -> Period:
    return Period(
        key=PeriodKey.TODAY, start=today, end=today, label="Today", phrase="today"
    )


def _week(*, monday: date, key: PeriodKey, label: str) -> Period:
    """Weeks start on Monday (PRD assumption under FR-28)."""
    return Period(
        key=key,
        start=monday,
        end=monday + timedelta(days=6),
        label=label,
        phrase=label.lower(),
    )


def _this_week(today: date) -> Period:
    monday = today - timedelta(days=today.weekday())
    return _week(monday=monday, key=PeriodKey.THIS_WEEK, label="This week")


def _last_week(today: date) -> Period:
    monday = today - timedelta(days=today.weekday() + 7)
    return _week(monday=monday, key=PeriodKey.LAST_WEEK, label="Last week")


def _last_month(today: date) -> Period:
    first = _month_before(first=today.replace(day=1))
    return _named_month(first=first, key=PeriodKey.LAST_MONTH)


def _this_month(today: date) -> Period:
    first = today.replace(day=1)
    # "so far", as SummaryStates draws; the range still runs to the month's
    # end, so a confirmed future expense counts (PRD assumption under FR-22).
    return Period(
        key=PeriodKey.THIS_MONTH,
        start=first,
        end=_last_day(first=first),
        label=f"{_month_label(first=first)} so far",
        phrase="this month",
    )


def _this_year(today: date) -> Period:
    return Period(
        key=PeriodKey.THIS_YEAR,
        start=date(today.year, 1, 1),
        end=date(today.year, 12, 31),
        label=f"{today.year} so far",
        phrase="this year",
    )


def _most_recent_month(*, month: int, today: date) -> Period:
    """A month without a year is the most recent one not after today (PRD
    assumption under FR-28). This month's own name reads as this month."""
    if month == today.month:
        return _this_month(today)
    year = today.year if month < today.month else today.year - 1
    return _named_month(first=date(year, month, 1), key=PeriodKey.MONTH)


def _named_month(*, first: date, key: PeriodKey) -> Period:
    label = _month_label(first=first)
    return Period(
        key=key,
        start=first,
        end=_last_day(first=first),
        label=label,
        phrase=f"in {label}",
    )


def _month_before(*, first: date) -> date:
    return (first - timedelta(days=1)).replace(day=1)


def _last_day(*, first: date) -> date:
    return first.replace(day=calendar.monthrange(first.year, first.month)[1])


def _month_label(*, first: date) -> str:
    return f"{_MONTH_NAMES[first.month - 1]} {first.year}"


_FIXED_PERIODS: dict[str, Callable[[date], Period]] = {
    "": _this_month,
    "this month": _this_month,
    "today": _today,
    "this week": _this_week,
    "last week": _last_week,
    "last month": _last_month,
    "this year": _this_year,
}
