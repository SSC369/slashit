"""Reminders' queries: the grouped tab and one reminder's detail."""

from typing import Annotated, cast
from uuid import UUID

import strawberry
from strawberry.types import Info

from app.core.context import Context
from app.core.deps import build_get_reminder_interactor, build_list_reminders_interactor
from app.domains.reminders.graphql.errors import ReminderNotFound
from app.domains.reminders.graphql.types import ReminderGroups, reminder_groups_to_type
from app.domains.reminders.interactors.dtos import (
    GetReminderInputDTO,
    ListRemindersInputDTO,
)
from app.domains.reminders.interfaces.dtos import Reminder, reminder_dto_to_type
from app.graphql.error_mapping import map_errors
from app.graphql.permissions import IsAuthenticated

ReminderResult = Annotated[
    Reminder | ReminderNotFound, strawberry.union("ReminderResult")
]


@strawberry.type
class ReminderQueries:
    @strawberry.field(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    async def reminders(self, info: Info, search: str | None = None) -> ReminderGroups:
        context = cast(Context, info.context)
        user_id = cast(UUID, context.user_id)
        interactor = build_list_reminders_interactor(context)
        groups = await interactor.list_reminders(
            dto=ListRemindersInputDTO(user_id=user_id, search=search)
        )
        return reminder_groups_to_type(groups=groups)

    @strawberry.field(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    @map_errors
    async def reminder(
        self,
        info: Info,
        id_: Annotated[strawberry.ID, strawberry.argument(name="id")],
    ) -> ReminderResult:
        context = cast(Context, info.context)
        user_id = cast(UUID, context.user_id)
        interactor = build_get_reminder_interactor(context)
        reminder = await interactor.get_reminder(
            dto=GetReminderInputDTO(user_id=user_id, reminder_id=UUID(str(id_)))
        )
        return cast(ReminderResult, reminder_dto_to_type(reminder=reminder))
