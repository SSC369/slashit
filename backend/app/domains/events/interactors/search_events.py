"""FR-30: the user's live events a search matches, presented, for 005's
search through its SearchPort. Ranking is search's, not decided here."""

from collections.abc import Callable, Sequence
from datetime import datetime
from uuid import UUID

from app.domains.events.interfaces.dtos import EventSearchMatchDTO, EventSearchPageDTO
from app.domains.events.interfaces.ports import UserClockPort
from app.domains.events.interfaces.repositories import EventRepository
from app.domains.events.services.presenter import present_event


class SearchEventsInteractor:
    def __init__(
        self,
        *,
        event_repository: EventRepository,
        user_clock: UserClockPort,
        now_provider: Callable[[], datetime],
    ) -> None:
        self.event_repository = event_repository
        self.user_clock = user_clock
        self.now_provider = now_provider

    async def search_events(
        self,
        *,
        user_id: UUID,
        terms: Sequence[str],
        query_embedding: Sequence[float] | None,
        max_distance: float,
        limit: int,
    ) -> EventSearchPageDTO:
        """Words over title, location and description, and meaning over their
        vector (005 AD-2). Nothing raises: no match is an empty page."""
        page = await self.event_repository.search_events(
            user_id=user_id,
            terms=terms,
            query_embedding=query_embedding,
            max_distance=max_distance,
            limit=limit,
        )
        clock = await self.user_clock.get_user_clock(user_id=user_id)
        now = self.now_provider()
        return EventSearchPageDTO(
            matches=[
                EventSearchMatchDTO(
                    event=present_event(stored=match.event, clock=clock, now=now),
                    all_terms=match.all_terms,
                    word_rank=match.word_rank,
                    distance=match.distance,
                )
                for match in page.matches
            ],
            total=page.total,
        )
