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
