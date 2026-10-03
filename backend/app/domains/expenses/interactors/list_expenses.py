"""FR-16, FR-17: the Expenses tab, filtered by category and, from slice 2, by
period."""

from app.domains.expenses.interactors.dtos import ListExpensesInputDTO
from app.domains.expenses.interfaces.dtos import ExpenseDTO
from app.domains.expenses.interfaces.repositories import ExpenseRepository


class ListExpensesInteractor:
    def __init__(self, *, expense_repository: ExpenseRepository) -> None:
        self.expense_repository = expense_repository

    async def list_expenses(self, *, dto: ListExpensesInputDTO) -> list[ExpenseDTO]:
        """The caller's live expenses, newest ``spent_on`` first."""
        return await self.expense_repository.list_for_user(
            user_id=dto.user_id, category=dto.category, start=dto.start, end=dto.end
        )
