"""The only SQL in the expenses domain. Returns DTOs, never models."""

import uuid
from datetime import UTC, date, datetime
from typing import cast

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import user_transaction
from app.domains.expenses.interfaces.dtos import (
    CategoryTotal,
    ExpenseCategory,
    ExpenseChanges,
    ExpenseDTO,
    ExpenseOriginValue,
)
from app.domains.expenses.interfaces.repositories import ExpenseWrite
from app.domains.expenses.models import Expense


class SqlExpenseRepository:
    """Reads and writes ``expenses`` against the request's own session."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_expense(
        self, *, user_id: uuid.UUID, write: ExpenseWrite
    ) -> ExpenseDTO:
        now = datetime.now(UTC)
        expense = Expense(
            id=uuid.uuid4(),
            user_id=user_id,
            amount_paise=write.amount_paise,
            description=write.description,
            category=write.category.value,
            spent_on=write.spent_on,
            origin=write.origin,
            original_input=write.original_input,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )
        async with user_transaction(self.session, user_id) as scoped:
            scoped.add(expense)
        return _expense_to_dto(expense=expense)

    async def get_by_id(
        self, *, user_id: uuid.UUID, expense_id: uuid.UUID
    ) -> ExpenseDTO | None:
        async with user_transaction(self.session, user_id) as scoped:
            expense = await scoped.scalar(
                _live_for(user_id=user_id).where(Expense.id == expense_id)
            )
            return _expense_to_dto(expense=expense) if expense else None

    async def list_for_user(
        self,
        *,
        user_id: uuid.UUID,
        category: ExpenseCategory | None,
        start: date | None,
        end: date | None,
    ) -> list[ExpenseDTO]:
        query = _live_for(user_id=user_id)
        if category is not None:
            query = query.where(Expense.category == category.value)
        if start is not None:
            query = query.where(Expense.spent_on >= start)
        if end is not None:
            query = query.where(Expense.spent_on <= end)
        query = query.order_by(
            Expense.spent_on.desc(), Expense.created_at.desc(), Expense.id.desc()
        )
        async with user_transaction(self.session, user_id) as scoped:
            expenses = (await scoped.scalars(query)).all()
            return [_expense_to_dto(expense=expense) for expense in expenses]

    async def update_expense(
        self, *, user_id: uuid.UUID, expense_id: uuid.UUID, changes: ExpenseChanges
    ) -> ExpenseDTO | None:
        async with user_transaction(self.session, user_id) as scoped:
            expense = await scoped.scalar(
                _live_for(user_id=user_id)
                .where(Expense.id == expense_id)
                .with_for_update()
            )
            if expense is None:
                return None
            if changes.amount_paise is not None:
                expense.amount_paise = changes.amount_paise
            if changes.description is not None:
                if changes.description != expense.description:
                    # The old vector describes the old words (index §4).
                    expense.embedding = None
                expense.description = changes.description
            if changes.category is not None:
                expense.category = changes.category.value
            if changes.spent_on is not None:
                expense.spent_on = changes.spent_on
            expense.updated_at = datetime.now(UTC)
            await scoped.flush()
            return _expense_to_dto(expense=expense)

    async def sum_by_category(
        self,
        *,
        user_id: uuid.UUID,
        start: date | None,
        end: date | None,
        category: ExpenseCategory | None,
    ) -> list[CategoryTotal]:
        # Integer paise summed in PostgreSQL: exact to the paisa (NFR-6, AD-2).
        query = (
            select(
                Expense.category,
                func.sum(Expense.amount_paise),
                func.count(Expense.id),
            )
            .where(Expense.user_id == user_id, Expense.deleted_at.is_(None))
            .group_by(Expense.category)
        )
        if category is not None:
            query = query.where(Expense.category == category.value)
        if start is not None:
            query = query.where(Expense.spent_on >= start)
        if end is not None:
            query = query.where(Expense.spent_on <= end)
        async with user_transaction(self.session, user_id) as scoped:
            rows = (await scoped.execute(query)).all()
            return [
                CategoryTotal(
                    category=ExpenseCategory(row_category),
                    total_paise=int(total_paise),
                    count=int(row_count),
                )
                for row_category, total_paise, row_count in rows
            ]

    async def soft_delete(self, *, user_id: uuid.UUID, expense_id: uuid.UUID) -> bool:
        async with user_transaction(self.session, user_id) as scoped:
            expense = await scoped.scalar(
                _live_for(user_id=user_id)
                .where(Expense.id == expense_id)
                .with_for_update()
            )
            if expense is None:
                return False
            expense.deleted_at = datetime.now(UTC)
            return True


def _live_for(*, user_id: uuid.UUID) -> Select[tuple[Expense]]:
    return select(Expense).where(
        Expense.user_id == user_id, Expense.deleted_at.is_(None)
    )


def _expense_to_dto(*, expense: Expense) -> ExpenseDTO:
    return ExpenseDTO(
        id=expense.id,
        user_id=expense.user_id,
        amount_paise=expense.amount_paise,
        description=expense.description,
        category=ExpenseCategory(expense.category),
        spent_on=expense.spent_on,
        origin=cast(ExpenseOriginValue, expense.origin),
        original_input=expense.original_input,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
    )
