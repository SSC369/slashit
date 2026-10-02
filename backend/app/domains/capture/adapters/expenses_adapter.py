"""Implements capture's ExpensePort against the expenses domain."""

from uuid import UUID

from app.domains.expenses.public import ExpenseDTO, ExpenseFields, ExpenseService


class ExpensesAdapter:
    def __init__(self, *, expense_service: ExpenseService) -> None:
        self.expense_service = expense_service

    async def create_expense(
        self, *, user_id: UUID, fields: ExpenseFields, original_input: str
    ) -> ExpenseDTO:
        return await self.expense_service.create_expense(
            user_id=user_id, fields=fields, original_input=original_input
        )
