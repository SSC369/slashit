"""The only SQL in the expenses domain. Returns DTOs, never models."""

import uuid
from collections.abc import Sequence
from datetime import UTC, date, datetime
from typing import Any, cast

from sqlalchemy import (
    ColumnElement,
    Float,
    Select,
    case,
    false,
    func,
    or_,
    select,
    update,
)
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import user_transaction
from app.core.text_search import build_search_expressions
from app.domains.expenses.interfaces.dtos import (
    CategoryTotal,
    ExpenseCategory,
    ExpenseChanges,
    ExpenseDTO,
    ExpenseEmbeddingTargetDTO,
    ExpenseOriginValue,
    ExpenseSearchMatchDTO,
    ExpenseSearchPageDTO,
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

    # Epic 006, sub-plan 4.3.
    async def search_expenses(
        self,
        *,
        user_id: uuid.UUID,
        terms: Sequence[str],
        amount_paise: int | None,
        query_embedding: Sequence[float] | None,
        max_distance: float,
        limit: int,
    ) -> ExpenseSearchPageDTO:
        """Live expenses matching any term, the exact amount, or within
        ``max_distance``. Ordered for the database's own cut at ``limit``
        only; search ranks (005 AD-3)."""
        expressions = build_search_expressions(
            search_vector=Expense.search_vector,
            embedding=Expense.embedding,
            terms=terms,
            query_embedding=query_embedding,
            max_distance=max_distance,
        )
        conditions: list[ColumnElement[bool]] = []
        if expressions.matches is not None:
            conditions.append(expressions.matches)
        amount_match: ColumnElement[bool] = false()
        if amount_paise is not None:
            amount_match = Expense.amount_paise == amount_paise
            conditions.append(amount_match)
        if not conditions:
            return ExpenseSearchPageDTO(matches=[], total=0)
        # 4.3 Q2: an exact amount sits in the top tier, with every-word
        # matches, and sorts with word matches rather than after them.
        all_terms = or_(expressions.all_terms, amount_match)
        word_rank = func.coalesce(
            expressions.word_rank,
            case((amount_match, 1.0), else_=None).cast(Float),
        )
        live_matches = (
            Expense.user_id == user_id,
            Expense.deleted_at.is_(None),
            or_(*conditions),
        )
        ordering: list[Any] = list(expressions.ordering)
        if amount_paise is not None:
            ordering.insert(0, amount_match.desc())
        statement = (
            select(Expense, all_terms, word_rank, expressions.distance)
            .where(*live_matches)
            .order_by(*ordering, Expense.id)
            .limit(limit)
        )
        async with user_transaction(self.session, user_id) as scoped:
            rows = (await scoped.execute(statement)).all()
            total = await scoped.scalar(
                select(func.count()).select_from(Expense).where(*live_matches)
            )
        return ExpenseSearchPageDTO(
            matches=[
                ExpenseSearchMatchDTO(
                    expense=_expense_to_dto(expense=expense),
                    all_terms=bool(is_all),
                    word_rank=rank,
                    distance=distance,
                )
                for expense, is_all, rank, distance in rows
            ],
            total=int(total or 0),
        )

    async def get_embedding(
        self, *, user_id: uuid.UUID, expense_id: uuid.UUID
    ) -> tuple[float, ...] | None:
        async with user_transaction(self.session, user_id) as scoped:
            embedding = await scoped.scalar(
                select(Expense.embedding).where(
                    Expense.id == expense_id,
                    Expense.user_id == user_id,
                    Expense.deleted_at.is_(None),
                )
            )
        return None if embedding is None else tuple(float(item) for item in embedding)

    async def get_description_needing_embedding(
        self, *, user_id: uuid.UUID, expense_id: uuid.UUID
    ) -> str | None:
        """The live expense's description while it has no vector, else None:
        gone, or already embedded, as after an edit that kept the words."""
        async with user_transaction(self.session, user_id) as scoped:
            description = await scoped.scalar(
                select(Expense.description).where(
                    Expense.id == expense_id,
                    Expense.user_id == user_id,
                    Expense.deleted_at.is_(None),
                    Expense.embedding.is_(None),
                )
            )
        return None if description is None else str(description)

    async def set_embedding(
        self,
        *,
        user_id: uuid.UUID,
        expense_id: uuid.UUID,
        description: str,
        embedding: Sequence[float],
    ) -> bool:
        """Store the vector only if the description is still the one embedded,
        so a vector computed before a later edit is never written over it."""
        async with user_transaction(self.session, user_id) as scoped:
            result = cast(
                CursorResult[Any],
                await scoped.execute(
                    update(Expense)
                    .where(
                        Expense.id == expense_id,
                        Expense.user_id == user_id,
                        Expense.deleted_at.is_(None),
                        Expense.description == description,
                    )
                    .values(embedding=list(embedding))
                ),
            )
        return result.rowcount > 0

    async def select_missing_embeddings(
        self,
        *,
        updated_since: datetime | None,
        after_id: uuid.UUID | None,
        limit: int,
    ) -> list[ExpenseEmbeddingTargetDTO]:
        """Every user's live expenses with no vector. ``updated_since`` None
        means every such expense, for the full sweep at deploy."""
        statement = select(Expense.user_id, Expense.id).where(
            Expense.embedding.is_(None), Expense.deleted_at.is_(None)
        )
        if updated_since is not None:
            statement = statement.where(Expense.updated_at >= updated_since)
        if after_id is not None:
            statement = statement.where(Expense.id > after_id)
        # No user_transaction: the sweep reads every user's rows on the
        # service-role connection, as a background job may (T3).
        async with self.session.begin():
            rows = (
                await self.session.execute(statement.order_by(Expense.id).limit(limit))
            ).all()
        return [
            ExpenseEmbeddingTargetDTO(user_id=owner_id, expense_id=expense_id)
            for owner_id, expense_id in rows
        ]


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
