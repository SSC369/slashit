"""Events' queries: the upcoming or full list, and one event's detail."""

from enum import Enum
from typing import Annotated, cast
from uuid import UUID

import strawberry
from strawberry.types import Info

from app.core.context import Context
from app.core.deps import build_get_event_interactor, build_list_events_interactor
from app.domains.events.graphql.errors import EventNotFound
from app.domains.events.interactors.dtos import GetEventInputDTO, ListEventsInputDTO
from app.domains.events.interfaces.dtos import Event, event_dto_to_type
from app.graphql.error_mapping import map_errors
from app.graphql.permissions import IsAuthenticated

EventResult = Annotated[Event | EventNotFound, strawberry.union("EventResult")]


@strawberry.enum
class EventScope(Enum):
    """UPCOMING is `/events` (FR-24); ALL is the Records Events tab (FR-25)."""

    UPCOMING = "upcoming"
    ALL = "all"


@strawberry.type
class EventQueries:
    @strawberry.field(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    async def events(
        self, info: Info, scope: EventScope = EventScope.UPCOMING
    ) -> list[Event]:
        context = cast(Context, info.context)
        user_id = cast(UUID, context.user_id)
        interactor = build_list_events_interactor(context)
        dto = ListEventsInputDTO(user_id=user_id)
        if scope == EventScope.ALL:
            events = await interactor.list_for_records(dto=dto)
        else:
            events = await interactor.list_upcoming(dto=dto)
        return [event_dto_to_type(event=event) for event in events]

    @strawberry.field(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    @map_errors
    async def event(
        self,
        info: Info,
        id_: Annotated[strawberry.ID, strawberry.argument(name="id")],
    ) -> EventResult:
        context = cast(Context, info.context)
        user_id = cast(UUID, context.user_id)
        interactor = build_get_event_interactor(context)
        event = await interactor.get_event(
            dto=GetEventInputDTO(user_id=user_id, event_id=UUID(str(id_)))
        )
        return cast(EventResult, event_dto_to_type(event=event))
