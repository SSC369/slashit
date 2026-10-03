"""Data crossing the expenses domain's boundaries. Frozen, never a model.

The GraphQL shapes ``Expense`` and ``Paise`` live here rather than under
``graphql/`` so they may cross into ``capture`` and ``records`` through
``public.py``, the placement ``records`` uses for ``Task`` (repo-rules.md
section 6.2).
"""

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Literal, NewType
from uuid import UUID

import strawberry

ExpenseOriginValue = Literal["command", "edit"]


@strawberry.enum
class ExpenseCategory(StrEnum):
    """FR-9: the fixed eight."""

    FOOD = "food"
    TRANSPORT = "transport"
    SHOPPING = "shopping"
    BILLS = "bills"
    HEALTH = "health"
    ENTERTAINMENT = "entertainment"
    TRAVEL = "travel"
    OTHER = "other"


def _parse_paise(raw: object) -> int:
    """A decimal string of whole paise. Anything else is a client bug."""
    if not isinstance(raw, str) or not raw.lstrip("-").isdigit():
        raise ValueError("Paise must be a decimal string of whole paise")
    return int(raw)


# Index §4: GraphQL's Int is 32-bit and would cap an amount near ₹2.1 crore,
# against FR-2's no-limit rule, so money crosses as a decimal string. Fields
# are typed ``Paise``; ``PAISE_SCALAR`` is mapped to it in ``graphql/schema.py``.
Paise = NewType("Paise", int)

PAISE_SCALAR = strawberry.scalar(
    name="Paise",
    description="An amount in whole paise, as a decimal string.",
    serialize=str,
    parse_value=_parse_paise,
)


@dataclass(frozen=True)
class ExpenseFields:
    """What a capture read from one sentence, ready to save."""

    amount_paise: int
    description: str
    category: ExpenseCategory
    spent_on: date


@dataclass(frozen=True)
class ExpenseDTO:
    """One live expense, as every layer above the repository sees it."""

    id: UUID
    user_id: UUID
    amount_paise: int
    description: str
    category: ExpenseCategory
    spent_on: date
    origin: ExpenseOriginValue
    original_input: str
    created_at: datetime
    updated_at: datetime


@strawberry.enum(name="ExpensePeriodKey")
class PeriodKey(StrEnum):
    """FR-23's periods, and All time from the picker (sub-plan 4.2)."""

    TODAY = "today"
    THIS_WEEK = "this_week"
    LAST_WEEK = "last_week"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    MONTH = "month"
    THIS_YEAR = "this_year"
    ALL_TIME = "all_time"


@dataclass(frozen=True)
class Period:
    key: PeriodKey
    # None only for ALL_TIME, which only the picker offers (decision 2A).
    start: date | None
    end: date | None  # inclusive
    label: str  # the card's pill and the band: "September 2026"
    phrase: str  # FR-26's sentence: "last week", "in September 2026"


@dataclass(frozen=True)
class CategoryTotal:
    """One category's sum over a range. Never zero: an empty category has no
    row (FR-25)."""

    category: ExpenseCategory
    total_paise: int
    count: int


@dataclass(frozen=True)
class ExpenseSummaryDTO:
    """FR-23 and FR-18's totals for one range, sub-plan 4.2 §5."""

    label: str
    phrase: str
    start: date | None
    end: date | None
    category: ExpenseCategory | None
    totals: list[CategoryTotal]  # largest first, ties in FR-9's order
    grand_total_paise: int
    count: int


@dataclass(frozen=True)
class PeriodNotUnderstood:
    """FR-27: the text after ``/expenses`` is not on FR-23's list."""

    text: str


@dataclass(frozen=True)
class ExpenseSearchMatchDTO:
    """One expense a search matched, with the scores search ranks by (005
    AD-3). ``word_rank`` is None when no term is present; ``distance`` is None
    when the expense has no vector yet or the search had none. An exact amount
    match counts as every term present (sub-plan 4.3 Q2)."""

    expense: ExpenseDTO
    all_terms: bool
    word_rank: float | None
    distance: float | None


@dataclass(frozen=True)
class ExpenseSearchPageDTO:
    matches: list[ExpenseSearchMatchDTO]
    total: int


@dataclass(frozen=True)
class ExpenseEmbeddingTargetDTO:
    """An expense the embed backfill should queue: owner and id only."""

    user_id: UUID
    expense_id: UUID


@dataclass(frozen=True)
class ExpenseChanges:
    """An edit. Every field is optional; None means unchanged (FR-21)."""

    amount_paise: int | None = None
    description: str | None = None
    category: ExpenseCategory | None = None
    spent_on: date | None = None


@strawberry.type
class Expense:
    """FR-20: every stored field the detail shows."""

    id: strawberry.ID
    amount_paise: Paise
    description: str
    category: ExpenseCategory
    spent_on: date
    origin: str
    original_input: str
    created_at: datetime
    updated_at: datetime


def expense_dto_to_type(*, expense: ExpenseDTO) -> Expense:
    return Expense(
        id=strawberry.ID(str(expense.id)),
        amount_paise=Paise(expense.amount_paise),
        description=expense.description,
        category=expense.category,
        spent_on=expense.spent_on,
        origin=expense.origin,
        original_input=expense.original_input,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
    )


@strawberry.type
class ExpensePeriod:
    """One option of the Records period picker, resolved by the server so it
    sums exactly as ``/expenses`` does (FR-28, sub-plan 4.2 decision 3A)."""

    key: PeriodKey
    label: str
    phrase: str
    start: date | None
    end: date | None


@strawberry.type
class ExpenseCategoryTotal:
    category: ExpenseCategory
    total_paise: Paise


@strawberry.type
class ExpenseSummary:
    """FR-18 and FR-23: per-category totals, largest first, for one range."""

    label: str
    phrase: str
    start: date | None
    end: date | None
    count: int
    grand_total_paise: Paise
    totals: list[ExpenseCategoryTotal]


def period_to_type(*, period: Period) -> ExpensePeriod:
    return ExpensePeriod(
        key=period.key,
        label=period.label,
        phrase=period.phrase,
        start=period.start,
        end=period.end,
    )


def expense_summary_dto_to_type(*, summary: ExpenseSummaryDTO) -> ExpenseSummary:
    return ExpenseSummary(
        label=summary.label,
        phrase=summary.phrase,
        start=summary.start,
        end=summary.end,
        count=summary.count,
        grand_total_paise=Paise(summary.grand_total_paise),
        totals=[
            ExpenseCategoryTotal(
                category=total.category, total_paise=Paise(total.total_paise)
            )
            for total in summary.totals
        ],
    )
