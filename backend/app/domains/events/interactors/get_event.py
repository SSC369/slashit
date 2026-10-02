"""FR-27: one event's detail."""

from collections.abc import Callable
from datetime import datetime

from app.domains.events.graphql.errors import EventNotFoundError
from app.domains.events.interactors.dtos import GetEventInputDTO
from app.domains.events.interfaces.dtos import EventDTO
from app.domains.events.interfaces.ports import UserClockPort
from app.domains.events.interfaces.repositories import EventRepository
from app.domains.events.services.presenter import present_event


class GetEventInteractor:
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

    async def get_event(self, *, dto: GetEventInputDTO) -> EventDTO:
        """Return one live event the caller owns.

        Raises:
            EventNotFoundError: no live event with this id is theirs. Deleted
                and another user's read the same (NFR-6).
        """
        stored = await self.event_repository.get_by_id(
            user_id=dto.user_id, event_id=dto.event_id
        )
        if stored is None:
            raise EventNotFoundError()
        clock = await self.user_clock.get_user_clock(user_id=dto.user_id)
        return present_event(stored=stored, clock=clock, now=self.now_provider())
