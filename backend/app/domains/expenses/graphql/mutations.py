"""Expenses' mutations: edit (FR-21) and delete (FR-22), from Records only."""

from typing import Annotated, cast
from uuid import UUID

import strawberry
from strawberry.types import Info

from app.core.context import Context
from app.core.deps import (
    build_delete_expense_interactor,
    build_update_expense_interactor,
)
from app.domains.expenses.graphql.errors import ExpenseInvalid, ExpenseNotFound
from app.domains.expenses.graphql.inputs import UpdateExpenseInput
from app.domains.expenses.graphql.types import ExpenseDeleted
from app.domains.expenses.interactors.dtos import (
    DeleteExpenseInputDTO,
    UpdateExpenseInputDTO,
)
from app.domains.expenses.interfaces.dtos import (
    Expense,
    ExpenseChanges,
    expense_dto_to_type,
)
from app.graphql.error_mapping import map_errors
from app.graphql.permissions import IsAuthenticated

UpdateExpenseResult = Annotated[
    Expense | ExpenseNotFound | ExpenseInvalid,
    strawberry.union("UpdateExpenseResult"),
]
DeleteExpenseResult = Annotated[
    ExpenseDeleted | ExpenseNotFound, strawberry.union("DeleteExpenseResult")
]


@strawberry.type
class ExpenseMutations:
    @strawberry.mutation(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    @map_errors
    async def update_expense(
        self,
        info: Info,
        id_: Annotated[strawberry.ID, strawberry.argument(name="id")],
        input_: Annotated[UpdateExpenseInput, strawberry.argument(name="input")],
    ) -> UpdateExpenseResult:
        context = cast(Context, info.context)
        user_id = cast(UUID, context.user_id)
        interactor = build_update_expense_interactor(context)
        expense = await interactor.update_expense(
            dto=UpdateExpenseInputDTO(
                user_id=user_id,
                expense_id=UUID(str(id_)),
                changes=ExpenseChanges(
                    amount_paise=input_.amount_paise,
                    description=input_.description,
                    category=input_.category,
                    spent_on=input_.spent_on,
                ),
            )
        )
        return cast(UpdateExpenseResult, expense_dto_to_type(expense=expense))

    @strawberry.mutation(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    @map_errors
    async def delete_expense(
        self,
        info: Info,
        id_: Annotated[strawberry.ID, strawberry.argument(name="id")],
    ) -> DeleteExpenseResult:
        context = cast(Context, info.context)
        user_id = cast(UUID, context.user_id)
        interactor = build_delete_expense_interactor(context)
        await interactor.delete_expense(
            dto=DeleteExpenseInputDTO(user_id=user_id, expense_id=UUID(str(id_)))
        )
        return cast(DeleteExpenseResult, ExpenseDeleted(id=id_))
