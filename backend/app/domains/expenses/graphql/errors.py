"""Expenses' failure outcomes, as union members and exceptions together.

Both faces of an error live in this one file, per repo-rules.md sections 7.1
and 8.
"""

from enum import StrEnum
from uuid import UUID

import strawberry

from app.core.errors import DomainError
from app.domains.expenses.constants import MAX_DESCRIPTION_LENGTH


@strawberry.type
class ExpenseNotFound:
    message: str


class ExpenseNotFoundError(DomainError):
    """Unknown, deleted and another user's expense all read the same (NFR-1)."""

    gql_type = ExpenseNotFound

    def __init__(self) -> None:
        super().__init__("This expense no longer exists.")


def parse_expense_id(id_: strawberry.ID) -> UUID:
    """A hand-typed URL such as /records/expenses/abc names no expense, so it
    reads as one that does not exist, not as a server error (dev log E-1)."""
    try:
        return UUID(str(id_))
    except ValueError as error:
        raise ExpenseNotFoundError() from error


@strawberry.enum
class ExpenseField(StrEnum):
    AMOUNT = "amount"
    DESCRIPTION = "description"


@strawberry.enum
class ExpenseInvalidReason(StrEnum):
    NOT_POSITIVE = "not_positive"
    EMPTY = "empty"
    TOO_LONG = "too_long"
    # FR-2 as amended 2026-10-03: past the storage ceiling (dev log E-2).
    TOO_LARGE = "too_large"


@strawberry.type
class ExpenseInvalid:
    """FR-21: an edit broke FR-2 or FR-13. ``length`` is set for TOO_LONG."""

    message: str
    field: ExpenseField
    reason: ExpenseInvalidReason
    length: int | None


class ExpenseInvalidError(DomainError):
    gql_type = ExpenseInvalid

    def __init__(
        self,
        *,
        field: ExpenseField,
        reason: ExpenseInvalidReason,
        length: int | None = None,
    ) -> None:
        self.field = field
        self.reason = reason
        self.length = length
        super().__init__(_invalid_message(reason=reason, length=length))


def _invalid_message(*, reason: ExpenseInvalidReason, length: int | None) -> str:
    if reason == ExpenseInvalidReason.NOT_POSITIVE:
        return "Enter an amount above ₹0."
    if reason == ExpenseInvalidReason.TOO_LARGE:
        return "That amount is too large to save. Check it for an extra zero."
    if reason == ExpenseInvalidReason.EMPTY:
        return "Say what the expense was for."
    return (
        f"That description is {length} characters. "
        f"It can be up to {MAX_DESCRIPTION_LENGTH}."
    )
