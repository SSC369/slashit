"""Expenses' GraphQL inputs."""

from datetime import date

import strawberry

from app.domains.expenses.interfaces.dtos import ExpenseCategory, Paise


@strawberry.input
class ExpensesFilterInput:
    """FR-17. ``start`` and ``end`` are inclusive local dates; slice 2's
    period picker sends them."""

    category: ExpenseCategory | None = None
    start: date | None = None
    end: date | None = None


@strawberry.input
class UpdateExpenseInput:
    """FR-21. An omitted or null field is left unchanged."""

    amount_paise: Paise | None = None
    description: str | None = None
    category: ExpenseCategory | None = None
    spent_on: date | None = None
