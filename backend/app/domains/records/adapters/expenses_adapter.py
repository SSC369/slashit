"""Implements records' ExpenseRecordsPort against the expenses domain."""

from uuid import UUID

from app.domains.expenses.public import ExpenseDTO, ExpenseService


class ExpenseRecordsAdapter:
    def __init__(self, *, expense_service: ExpenseService) -> None:
        self.expense_service = expense_service

    async def list_expenses(self, *, user_id: UUID) -> list[ExpenseDTO]:
        return await self.expense_service.list_expenses(
            user_id=user_id, category=None, start=None, end=None
        )
