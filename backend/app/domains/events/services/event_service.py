"""The events domain's published surface.

Other domains reach events only through this class, re-exported from
``public.py`` and called through their own port and adapter (repo-rules.md
section 6). Each method delegates to the one use case that owns its rules.
"""

from collections.abc import Sequence
from uuid import UUID

from app.domains.events.interactors.create_event import (
    CreateEventInteractor,
    CreateEventOutcome,
)
from app.domains.events.interactors.dtos import CreateEventInputDTO, ListEventsInputDTO
from app.domains.events.interactors.list_events import ListEventsInteractor
from app.domains.events.interactors.search_events import SearchEventsInteractor
from app.domains.events.interfaces.dtos import (
    EventDTO,
    EventFields,
    EventSearchPageDTO,
    RecordOriginValue,
)
from app.domains.events.interfaces.repositories import EventRepository


class EventService:
    def __init__(
        self,
        *,
        create_event_interactor: CreateEventInteractor,
        list_events_interactor: ListEventsInteractor,
        search_events_interactor: SearchEventsInteractor,
        event_repository: EventRepository,
    ) -> None:
        self.create_event_interactor = create_event_interactor
        self.list_events_interactor = list_events_interactor
        self.search_events_interactor = search_events_interactor
        self.event_repository = event_repository

    async def create_event(
        self,
        *,
        user_id: UUID,
        fields: EventFields,
        origin: RecordOriginValue,
        original_input: str | None,
    ) -> CreateEventOutcome:
        return await self.create_event_interactor.create_event(
            dto=CreateEventInputDTO(
                user_id=user_id,
                fields=fields,
                origin=origin,
                original_input=original_input,
            )
        )

    async def list_upcoming(self, *, user_id: UUID) -> list[EventDTO]:
        """`/events`, FR-24."""
        return await self.list_events_interactor.list_upcoming(
            dto=ListEventsInputDTO(user_id=user_id)
        )

    async def list_for_records(self, *, user_id: UUID) -> list[EventDTO]:
        """Every live event, upcoming then past, for Records (FR-25, FR-26)."""
        return await self.list_events_interactor.list_for_records(
            dto=ListEventsInputDTO(user_id=user_id)
        )

    async def search_candidates(
        self,
        *,
        user_id: UUID,
        terms: Sequence[str],
        query_embedding: Sequence[float] | None,
        max_distance: float,
        limit: int,
    ) -> EventSearchPageDTO:
        """FR-30: the user's live events a search matches (005 AD-1)."""
        return await self.search_events_interactor.search_events(
            user_id=user_id,
            terms=terms,
            query_embedding=query_embedding,
            max_distance=max_distance,
            limit=limit,
        )

    async def embedding_of(
        self, *, user_id: UUID, event_id: UUID
    ) -> tuple[float, ...] | None:
        """The live event's stored vector, for related records (005 AD-6)."""
        return await self.event_repository.get_embedding(
            user_id=user_id, event_id=event_id
        )
