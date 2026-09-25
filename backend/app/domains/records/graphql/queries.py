"""Records' queries: the table, one row's detail, and the open-tasks list.

Read: context, build the interactor (or, for `tasks`, the published
`RecordsService` this domain already built in slice 1 — the same list
`/tasks` calls, exposed here as a first-class query), call it, convert.
"""

from typing import Annotated, cast
from uuid import UUID

import strawberry
from strawberry.types import Info

from app.core.context import Context
from app.core.deps import (
    build_get_record_detail_interactor,
    build_list_tasks_interactor,
    build_records_service,
)
from app.domains.records.graphql.errors import RecordNotFound
from app.domains.records.graphql.inputs import RecordsFilterInput
from app.domains.records.interactors.dtos import (
    GetRecordDetailInputDTO,
    ListTasksInputDTO,
)
from app.domains.records.interfaces.dtos import Task, TaskDTO, task_dto_to_type
from app.domains.reminders.public import Reminder, reminder_dto_to_type
from app.graphql.error_mapping import map_errors
from app.graphql.permissions import IsAuthenticated

RecordResult = Annotated[Task | RecordNotFound, strawberry.union("RecordResult")]
# Epic 003: the All tab lists both record types.
RecordItem = Annotated[Task | Reminder, strawberry.union("RecordItem")]


@strawberry.type
class RecordQueries:
    @strawberry.field(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    async def records(
        self,
        info: Info,
        filter_: Annotated[
            RecordsFilterInput | None, strawberry.argument(name="filter")
        ] = None,
    ) -> list[RecordItem]:
        context = cast(Context, info.context)
        user_id = cast(UUID, context.user_id)
        record_filter = filter_ or RecordsFilterInput()
        interactor = build_list_tasks_interactor(context)
        records = await interactor.list_tasks(
            dto=ListTasksInputDTO(
                user_id=user_id,
                kind_filter=record_filter.kind,
                search=record_filter.search,
                sort_by=record_filter.sort_by.value,
                sort_desc=record_filter.sort_desc,
            )
        )
        return [
            cast(RecordItem, task_dto_to_type(task=item))
            if isinstance(item, TaskDTO)
            else cast(RecordItem, reminder_dto_to_type(reminder=item))
            for item in records
        ]

    @strawberry.field(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    @map_errors
    async def record(
        self,
        info: Info,
        id_: Annotated[strawberry.ID, strawberry.argument(name="id")],
    ) -> RecordResult:
        context = cast(Context, info.context)
        user_id = cast(UUID, context.user_id)
        interactor = build_get_record_detail_interactor(context)
        task = await interactor.get_record_detail(
            dto=GetRecordDetailInputDTO(user_id=user_id, task_id=UUID(str(id_)))
        )
        return cast(RecordResult, task_dto_to_type(task=task))

    @strawberry.field(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    async def tasks(self, info: Info) -> list[Task]:
        context = cast(Context, info.context)
        user_id = cast(UUID, context.user_id)
        service = build_records_service(context)
        tasks = await service.list_open_tasks(user_id=user_id)
        return [task_dto_to_type(task=task) for task in tasks]
