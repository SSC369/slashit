"""FR-20: one expense's detail."""

from app.domains.expenses.graphql.errors import ExpenseNotFoundError
from app.domains.expenses.interactors.dtos import GetExpenseInputDTO
from app.domains.expenses.interfaces.dtos import ExpenseDTO
from app.domains.expenses.interfaces.repositories import ExpenseRepository


class GetExpenseInteractor:
    def __init__(self, *, expense_repository: ExpenseRepository) -> None:
        self.expense_repository = expense_repository

    async def get_expense(self, *, dto: GetExpenseInputDTO) -> ExpenseDTO:
        """Return one live expense the caller owns.

        Raises:
            ExpenseNotFoundError: no live expense with this id is theirs.
                Deleted and another user's read the same (NFR-1).
        """
        expense = await self.expense_repository.get_by_id(
            user_id=dto.user_id, expense_id=dto.expense_id
        )
        if expense is None:
            raise ExpenseNotFoundError()
        return expense
