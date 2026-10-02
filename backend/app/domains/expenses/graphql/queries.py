"""Expenses' queries: the Expenses tab and one expense's detail."""

from typing import Annotated, cast
from uuid import UUID

import strawberry
from strawberry.types import Info

from app.core.context import Context
from app.core.deps import build_get_expense_interactor, build_list_expenses_interactor
from app.domains.expenses.graphql.errors import ExpenseNotFound
from app.domains.expenses.graphql.inputs import ExpensesFilterInput
from app.domains.expenses.interactors.dtos import (
    GetExpenseInputDTO,
    ListExpensesInputDTO,
)
from app.domains.expenses.interfaces.dtos import Expense, expense_dto_to_type
from app.graphql.error_mapping import map_errors
from app.graphql.permissions import IsAuthenticated

ExpenseResult = Annotated[Expense | ExpenseNotFound, strawberry.union("ExpenseResult")]


@strawberry.type
class ExpenseQueries:
    @strawberry.field(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    async def expenses(
        self,
        info: Info,
        filter_: Annotated[
            ExpensesFilterInput | None, strawberry.argument(name="filter")
        ] = None,
    ) -> list[Expense]:
        context = cast(Context, info.context)
        user_id = cast(UUID, context.user_id)
        expenses_filter = filter_ or ExpensesFilterInput()
        interactor = build_list_expenses_interactor(context)
        expenses = await interactor.list_expenses(
            dto=ListExpensesInputDTO(
                user_id=user_id,
                category=expenses_filter.category,
                start=expenses_filter.start,
                end=expenses_filter.end,
            )
        )
        return [expense_dto_to_type(expense=expense) for expense in expenses]

    @strawberry.field(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    @map_errors
    async def expense(
        self,
        info: Info,
        id_: Annotated[strawberry.ID, strawberry.argument(name="id")],
    ) -> ExpenseResult:
        context = cast(Context, info.context)
        user_id = cast(UUID, context.user_id)
        interactor = build_get_expense_interactor(context)
        expense = await interactor.get_expense(
            dto=GetExpenseInputDTO(user_id=user_id, expense_id=UUID(str(id_)))
        )
        return cast(ExpenseResult, expense_dto_to_type(expense=expense))
