"""Reminders' mutations: edit and delete. Done and snooze arrive in slice 2."""

from datetime import time
from typing import Annotated, cast
from uuid import UUID

import strawberry
from strawberry.types import Info

from app.core.context import Context
from app.core.deps import (
    build_delete_reminder_interactor,
    build_update_reminder_interactor,
)
from app.domains.reminders.graphql.errors import (
    InvalidReminder,
    InvalidReminderError,
    ReminderDeleted,
    ReminderNotFound,
    ReminderTimePassed,
)
from app.domains.reminders.graphql.inputs import UpdateReminderInput
from app.domains.reminders.graphql.types import ReminderDeleteSucceeded
from app.domains.reminders.interactors.dtos import (
    DeleteReminderInputDTO,
    UpdateReminderInputDTO,
)
from app.domains.reminders.interfaces.dtos import Reminder, reminder_dto_to_type
from app.domains.reminders.services.schedule import RepeatKind
from app.graphql.error_mapping import map_errors
from app.graphql.permissions import IsAuthenticated

UpdateReminderResult = Annotated[
    Reminder
    | InvalidReminder
    | ReminderTimePassed
    | ReminderDeleted
    | ReminderNotFound,
    strawberry.union("UpdateReminderResult"),
]
DeleteReminderResult = Annotated[
    ReminderDeleteSucceeded | ReminderNotFound, strawberry.union("DeleteReminderResult")
]


def _parse_local_time(*, raw_time: str) -> time:
    """ "HH:MM" from the form. A malformed value is the form's bug, but it is
    still answered as a field error rather than a crash."""
    try:
        return time.fromisoformat(raw_time)
    except ValueError as error:
        raise InvalidReminderError(field="localTime", message="Pick a time.") from error


@strawberry.type
class ReminderMutations:
    @strawberry.mutation(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    @map_errors
    async def update_reminder(
        self,
        info: Info,
        id_: Annotated[strawberry.ID, strawberry.argument(name="id")],
        input_: Annotated[UpdateReminderInput, strawberry.argument(name="input")],
    ) -> UpdateReminderResult:
        context = cast(Context, info.context)
        user_id = cast(UUID, context.user_id)
        interactor = build_update_reminder_interactor(context)
        reminder = await interactor.update_reminder(
            dto=UpdateReminderInputDTO(
                user_id=user_id,
                reminder_id=UUID(str(id_)),
                description=input_.description,
                start_date=input_.start_date,
                local_time=_parse_local_time(raw_time=input_.local_time),
                repeat_kind=RepeatKind(input_.repeat_kind.value),
                repeat_interval=input_.repeat_interval,
                repeat_weekdays=tuple(input_.repeat_weekdays),
            )
        )
        return cast(UpdateReminderResult, reminder_dto_to_type(reminder=reminder))

    @strawberry.mutation(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    @map_errors
    async def delete_reminder(
        self,
        info: Info,
        id_: Annotated[strawberry.ID, strawberry.argument(name="id")],
    ) -> DeleteReminderResult:
        context = cast(Context, info.context)
        user_id = cast(UUID, context.user_id)
        interactor = build_delete_reminder_interactor(context)
        await interactor.delete_reminder(
            dto=DeleteReminderInputDTO(user_id=user_id, reminder_id=UUID(str(id_)))
        )
        return cast(DeleteReminderResult, ReminderDeleteSucceeded(id=id_))
