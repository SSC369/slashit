"""The only names other domains may import from expenses.

A domain's public surface is its contract. Adding a name here is a deliberate
act, reviewed like an API change. See backend/.claude/rules/repo-rules.md
section 6.
"""

from app.domains.expenses.constants import MAX_AMOUNT_PAISE, MAX_DESCRIPTION_LENGTH
from app.domains.expenses.interfaces.dtos import (
    PAISE_SCALAR,
    Expense,
    ExpenseCategory,
    ExpenseDTO,
    ExpenseFields,
    ExpenseSummary,
    ExpenseSummaryDTO,
    Paise,
    PeriodNotUnderstood,
    expense_dto_to_type,
    expense_summary_dto_to_type,
)
from app.domains.expenses.services.expense_service import ExpenseService

__all__ = [
    "MAX_AMOUNT_PAISE",
    "MAX_DESCRIPTION_LENGTH",
    "PAISE_SCALAR",
    "Expense",
    "ExpenseCategory",
    "ExpenseDTO",
    "ExpenseFields",
    "ExpenseService",
    "ExpenseSummary",
    "ExpenseSummaryDTO",
    "Paise",
    "PeriodNotUnderstood",
    "expense_dto_to_type",
    "expense_summary_dto_to_type",
]
