"""An in-memory ExpenseRepository, with the same ordering and soft delete as
the SQL one."""

import uuid
from dataclasses import replace
from datetime import UTC, date, datetime

from app.domains.expenses.interfaces.dtos import (
    ExpenseCategory,
    ExpenseChanges,
    ExpenseDTO,
)
from app.domains.expenses.interfaces.repositories import ExpenseWrite


class FakeExpenseRepository:
    def __init__(self) -> None:
        self.rows: dict[uuid.UUID, ExpenseDTO] = {}
        self.deleted: set[uuid.UUID] = set()
        self.cleared_embeddings: list[uuid.UUID] = []

    async def create_expense(
        self, *, user_id: uuid.UUID, write: ExpenseWrite
    ) -> ExpenseDTO:
        now = datetime.now(UTC)
        expense = ExpenseDTO(
            id=uuid.uuid4(),
            user_id=user_id,
            amount_paise=write.amount_paise,
            description=write.description,
            category=write.category,
            spent_on=write.spent_on,
            origin=write.origin,
            original_input=write.original_input,
            created_at=now,
            updated_at=now,
        )
        self.rows[expense.id] = expense
        return expense

    async def get_by_id(
        self, *, user_id: uuid.UUID, expense_id: uuid.UUID
    ) -> ExpenseDTO | None:
        expense = self.rows.get(expense_id)
        if expense is None or expense.user_id != user_id or expense_id in self.deleted:
            return None
        return expense

    async def list_for_user(
        self,
        *,
        user_id: uuid.UUID,
        category: ExpenseCategory | None,
        start: date | None,
        end: date | None,
    ) -> list[ExpenseDTO]:
        live = [
            expense
            for expense in self.rows.values()
            if expense.user_id == user_id
            and expense.id not in self.deleted
            and (category is None or expense.category == category)
            and (start is None or expense.spent_on >= start)
            and (end is None or expense.spent_on <= end)
        ]
        return sorted(
            live,
            key=lambda expense: (expense.spent_on, expense.created_at),
            reverse=True,
        )

    async def update_expense(
        self, *, user_id: uuid.UUID, expense_id: uuid.UUID, changes: ExpenseChanges
    ) -> ExpenseDTO | None:
        expense = await self.get_by_id(user_id=user_id, expense_id=expense_id)
        if expense is None:
            return None
        if (
            changes.description is not None
            and changes.description != expense.description
        ):
            self.cleared_embeddings.append(expense_id)
        updated = replace(
            expense,
            amount_paise=changes.amount_paise or expense.amount_paise,
            description=changes.description or expense.description,
            category=changes.category or expense.category,
            spent_on=changes.spent_on or expense.spent_on,
            updated_at=datetime.now(UTC),
        )
        self.rows[expense_id] = updated
        return updated

    async def soft_delete(self, *, user_id: uuid.UUID, expense_id: uuid.UUID) -> bool:
        if await self.get_by_id(user_id=user_id, expense_id=expense_id) is None:
            return False
        self.deleted.add(expense_id)
        return True
