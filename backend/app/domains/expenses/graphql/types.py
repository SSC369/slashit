"""Expenses' own success-shaped outcomes."""

import strawberry


@strawberry.type
class ExpenseDeleted:
    """FR-22: the expense left every view, count and total."""

    id: strawberry.ID
