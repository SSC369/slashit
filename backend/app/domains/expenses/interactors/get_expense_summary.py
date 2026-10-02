"""FR-18 and FR-28: the Records band's totals for the picked period and
category."""

from app.domains.expenses.interactors.dtos import GetExpenseSummaryInputDTO
from app.domains.expenses.interfaces.dtos import ExpenseSummaryDTO
from app.domains.expenses.services.expense_service import ExpenseService


class GetExpenseSummaryInteractor:
    def __init__(self, *, expense_service: ExpenseService) -> None:
        self.expense_service = expense_service

    async def get_expense_summary(
        self, *, dto: GetExpenseSummaryInputDTO
    ) -> ExpenseSummaryDTO:
        """The caller's totals over the range, largest first."""
        return await self.expense_service.summarise(
            user_id=dto.user_id, start=dto.start, end=dto.end, category=dto.category
        )
