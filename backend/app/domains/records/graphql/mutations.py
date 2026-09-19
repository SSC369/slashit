"""Records' mutations: update, complete, delete.

`completeTask` is not a separate business rule: it is `updateTask` with
`status` fixed to done, so it reuses `UpdateTaskInteractor` rather than
duplicating it.
"""

from typing import Annotated, cast
from uuid import UUID

import strawberry
from strawberry.types import Info

from app.core.context import Context
from app.core.deps import (
    build_delete_tasks_interactor,
    build_log_records_view_opened_interactor,
    build_update_task_interactor,
)
from app.domains.records.graphql.errors import NoFieldsToUpdate, RecordNotFound
from app.domains.records.graphql.inputs import UpdateTaskInput
from app.domains.records.graphql.types import TaskStatus
from app.domains.records.interactors.dtos import (
    DeleteTasksInputDTO,
    UpdateTaskInputDTO,
)
from app.domains.records.interfaces.dtos import Task, task_dto_to_type
from app.graphql.error_mapping import map_errors
from app.graphql.permissions import IsAuthenticated

UpdateTaskResult = Annotated[
    Task | NoFieldsToUpdate | RecordNotFound, strawberry.union("UpdateTaskResult")
]


@strawberry.type
class RecordMutations:
    @strawberry.mutation(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    @map_errors
    async def update_task(
        self,
        info: Info,
        id_: Annotated[strawberry.ID, strawberry.argument(name="id")],
        input_: Annotated[UpdateTaskInput, strawberry.argument(name="input")],
    ) -> UpdateTaskResult:
        context = cast(Context, info.context)
        user_id = cast(UUID, context.user_id)
        interactor = build_update_task_interactor(context)
        due_at_provided = input_.due_at is not strawberry.UNSET
        task = await interactor.update_task(
            dto=UpdateTaskInputDTO(
                user_id=user_id,
                task_id=UUID(str(id_)),
                title=input_.title,
                status=input_.status.value if input_.status is not None else None,
                due_at=input_.due_at if due_at_provided else None,
                due_at_provided=due_at_provided,
            )
        )
        return cast(UpdateTaskResult, task_dto_to_type(task=task))

    @strawberry.mutation(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    @map_errors
    async def complete_task(
        self,
        info: Info,
        id_: Annotated[strawberry.ID, strawberry.argument(name="id")],
    ) -> UpdateTaskResult:
        context = cast(Context, info.context)
        user_id = cast(UUID, context.user_id)
        interactor = build_update_task_interactor(context)
        task = await interactor.update_task(
            dto=UpdateTaskInputDTO(
                user_id=user_id,
                task_id=UUID(str(id_)),
                title=None,
                status=TaskStatus.DONE.value,
                due_at=None,
                due_at_provided=False,
            )
        )
        return cast(UpdateTaskResult, task_dto_to_type(task=task))

    @strawberry.mutation(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    async def delete_task(self, info: Info, ids: list[strawberry.ID]) -> int:
        context = cast(Context, info.context)
        user_id = cast(UUID, context.user_id)
        interactor = build_delete_tasks_interactor(context)
        return await interactor.delete_tasks(
            dto=DeleteTasksInputDTO(
                user_id=user_id, task_ids=[UUID(str(task_id)) for task_id in ids]
            )
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    async def records_view_opened(self, info: Info) -> bool:
        """The frontend calls this once when the records view mounts. PRD
        section 8's "weekly actives opening a records view" metric."""
        context = cast(Context, info.context)
        user_id = cast(UUID, context.user_id)
        interactor = build_log_records_view_opened_interactor(context)
        await interactor.log_records_view_opened(user_id=user_id)
        return True
