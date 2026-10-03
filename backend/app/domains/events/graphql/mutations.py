"""Events' mutations: edit (FR-28) and delete (FR-29), from Records."""

from datetime import time
from typing import Annotated, cast
from uuid import UUID

import strawberry
from strawberry.types import Info

from app.core.context import Context
from app.core.deps import build_delete_event_interactor, build_update_event_interactor
from app.domains.events.graphql.errors import (
    EventField,
    EventInvalid,
    EventInvalidError,
    EventInvalidReason,
    EventNotFound,
    parse_event_id,
)
from app.domains.events.graphql.inputs import EventInput
from app.domains.events.graphql.types import EventDeleted, EventUpdated
from app.domains.events.interactors.dtos import (
    DeleteEventInputDTO,
    UpdateEventInputDTO,
)
from app.domains.events.interfaces.dtos import (
    EventEdit,
    alert_not_set_to_type,
    event_dto_to_type,
)
from app.graphql.error_mapping import map_errors
from app.graphql.permissions import IsAuthenticated

UpdateEventResult = Annotated[
    EventUpdated | EventInvalid | EventNotFound,
    strawberry.union("UpdateEventResult"),
]
DeleteEventResult = Annotated[
    EventDeleted | EventNotFound, strawberry.union("DeleteEventResult")
]


@strawberry.type
class EventMutations:
    @strawberry.mutation(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    @map_errors
    async def update_event(
        self,
        info: Info,
        id_: Annotated[strawberry.ID, strawberry.argument(name="id")],
        input_: Annotated[EventInput, strawberry.argument(name="input")],
    ) -> UpdateEventResult:
        context = cast(Context, info.context)
        updated = await build_update_event_interactor(context).update_event(
            dto=UpdateEventInputDTO(
                user_id=cast(UUID, context.user_id),
                event_id=parse_event_id(id_),
                edit=_edit_from_input(input_=input_),
            )
        )
        return cast(
            UpdateEventResult,
            EventUpdated(
                event=event_dto_to_type(event=updated.event),
                alerts_not_set=[
                    alert_not_set_to_type(alert_not_set=alert_not_set)
                    for alert_not_set in updated.alerts_not_set
                ],
            ),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    @map_errors
    async def delete_event(
        self,
        info: Info,
        id_: Annotated[strawberry.ID, strawberry.argument(name="id")],
    ) -> DeleteEventResult:
        context = cast(Context, info.context)
        await build_delete_event_interactor(context).delete_event(
            dto=DeleteEventInputDTO(
                user_id=cast(UUID, context.user_id), event_id=parse_event_id(id_)
            )
        )
        return cast(DeleteEventResult, EventDeleted(id=id_))


def _edit_from_input(*, input_: EventInput) -> EventEdit:
    return EventEdit(
        title=input_.title,
        location=input_.location,
        description=input_.description,
        start_date=input_.start_date,
        start_time=_parse_clock(text=input_.start_time, field=EventField.DATE),
        end_date=input_.end_date,
        end_time=_parse_clock(text=input_.end_time, field=EventField.END),
        repeat_yearly=input_.repeat_yearly,
        alert_leads_minutes=tuple(input_.alert_leads_minutes),
    )


def _parse_clock(*, text: str | None, field: EventField) -> time | None:
    """ "HH:MM" from the form. Anything else is the form's defect, refused as
    an end before the start so nothing is stored."""
    if text is None:
        return None
    try:
        return time.fromisoformat(text[:5])
    except ValueError as error:
        raise EventInvalidError(
            field=field, reason=EventInvalidReason.END_BEFORE_START
        ) from error
