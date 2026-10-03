"""FR-17 and decision 3A: the Records period picker's options, resolved by
the server in the user's zone."""

from uuid import UUID

from app.domains.expenses.interfaces.dtos import Period
from app.domains.expenses.services.expense_service import ExpenseService


class ListExpensePeriodsInteractor:
    def __init__(self, *, expense_service: ExpenseService) -> None:
        self.expense_service = expense_service

    async def list_expense_periods(self, *, user_id: UUID) -> list[Period]:
        """Today to All time, in sub-plan 4.2 §5's order."""
        return await self.expense_service.periods(user_id=user_id)
