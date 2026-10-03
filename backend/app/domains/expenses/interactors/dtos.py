"""Input DTOs, one per use case."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from app.domains.expenses.interfaces.dtos import ExpenseCategory, ExpenseChanges


@dataclass(frozen=True)
class ListExpensesInputDTO:
    user_id: UUID
    category: ExpenseCategory | None
    start: date | None
    end: date | None


@dataclass(frozen=True)
class GetExpenseInputDTO:
    user_id: UUID
    expense_id: UUID


@dataclass(frozen=True)
class UpdateExpenseInputDTO:
    user_id: UUID
    expense_id: UUID
    changes: ExpenseChanges


@dataclass(frozen=True)
class DeleteExpenseInputDTO:
    user_id: UUID
    expense_id: UUID


@dataclass(frozen=True)
class GetExpenseSummaryInputDTO:
    user_id: UUID
    category: ExpenseCategory | None
    start: date | None
    end: date | None


@dataclass(frozen=True)
class EmbedExpenseInputDTO:
    user_id: UUID
    expense_id: UUID


@dataclass(frozen=True)
class QueueMissingExpenseEmbeddingsInputDTO:
    """``full`` sweeps every expense with no vector, once at deploy (sub-plan
    4.3 T-3.9); otherwise only expenses touched in the backfill window."""

    full: bool
