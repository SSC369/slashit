"""An in-memory ExpenseRepository, with the same ordering and soft delete as
the SQL one."""

import uuid
from collections.abc import Sequence
from dataclasses import replace
from datetime import UTC, date, datetime

from app.domains.expenses.interfaces.dtos import (
    CategoryTotal,
    ExpenseCategory,
    ExpenseChanges,
    ExpenseDTO,
    ExpenseEmbeddingTargetDTO,
)
from app.domains.expenses.interfaces.repositories import ExpenseWrite


class FakeExpenseRepository:
    def __init__(self) -> None:
        self.rows: dict[uuid.UUID, ExpenseDTO] = {}
        self.deleted: set[uuid.UUID] = set()
        self.cleared_embeddings: list[uuid.UUID] = []
        self.embeddings: dict[uuid.UUID, tuple[float, ...]] = {}

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
            self.embeddings.pop(expense_id, None)
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

    async def sum_by_category(
        self,
        *,
        user_id: uuid.UUID,
        start: date | None,
        end: date | None,
        category: ExpenseCategory | None,
    ) -> list[CategoryTotal]:
        expenses = await self.list_for_user(
            user_id=user_id, category=category, start=start, end=end
        )
        totals: dict[ExpenseCategory, CategoryTotal] = {}
        for expense in expenses:
            held = totals.get(expense.category)
            totals[expense.category] = CategoryTotal(
                category=expense.category,
                total_paise=(held.total_paise if held else 0) + expense.amount_paise,
                count=(held.count if held else 0) + 1,
            )
        return list(totals.values())

    async def get_embedding(
        self, *, user_id: uuid.UUID, expense_id: uuid.UUID
    ) -> tuple[float, ...] | None:
        if await self.get_by_id(user_id=user_id, expense_id=expense_id) is None:
            return None
        return self.embeddings.get(expense_id)

    async def get_description_needing_embedding(
        self, *, user_id: uuid.UUID, expense_id: uuid.UUID
    ) -> str | None:
        expense = await self.get_by_id(user_id=user_id, expense_id=expense_id)
        if expense is None or expense_id in self.embeddings:
            return None
        return expense.description

    async def set_embedding(
        self,
        *,
        user_id: uuid.UUID,
        expense_id: uuid.UUID,
        description: str,
        embedding: Sequence[float],
    ) -> bool:
        expense = await self.get_by_id(user_id=user_id, expense_id=expense_id)
        if expense is None or expense.description != description:
            return False
        self.embeddings[expense_id] = tuple(embedding)
        return True

    async def select_missing_embeddings(
        self,
        *,
        updated_since: datetime | None,
        after_id: uuid.UUID | None,
        limit: int,
    ) -> list[ExpenseEmbeddingTargetDTO]:
        missing = sorted(
            (
                expense
                for expense in self.rows.values()
                if expense.id not in self.deleted
                and expense.id not in self.embeddings
                and (updated_since is None or expense.updated_at >= updated_since)
                and (after_id is None or expense.id > after_id)
            ),
            key=lambda expense: expense.id,
        )
        return [
            ExpenseEmbeddingTargetDTO(user_id=expense.user_id, expense_id=expense.id)
            for expense in missing[:limit]
        ]
