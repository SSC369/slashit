"""FR-24 and FR-25: `/events` and the Records Events tab."""

from collections.abc import Callable
from datetime import datetime

from app.domains.events.interactors.dtos import ListEventsInputDTO
from app.domains.events.interfaces.dtos import EventDTO
from app.domains.events.interfaces.ports import UserClockPort
from app.domains.events.interfaces.repositories import EventRepository
from app.domains.events.services.presenter import present_event
from app.domains.events.services.schedule import EventStatus


class ListEventsInteractor:
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

    async def list_upcoming(self, *, dto: ListEventsInputDTO) -> list[EventDTO]:
        """Not yet ended, soonest first: yearly events at their next
        occurrence, multi-day events until their end (FR-24)."""
        events = await self._present_all(dto=dto)
        upcoming = [item for item in events if item.status != EventStatus.PAST]
        return sorted(upcoming, key=lambda item: item.starts_at)

    async def list_for_records(self, *, dto: ListEventsInputDTO) -> list[EventDTO]:
        """Upcoming soonest first, then past most recent first (FR-25)."""
        events = await self._present_all(dto=dto)
        upcoming = sorted(
            [item for item in events if item.status != EventStatus.PAST],
            key=lambda item: item.starts_at,
        )
        past = sorted(
            [item for item in events if item.status == EventStatus.PAST],
            key=lambda item: item.starts_at,
            reverse=True,
        )
        return [*upcoming, *past]

    async def _present_all(self, *, dto: ListEventsInputDTO) -> list[EventDTO]:
        stored_events = await self.event_repository.list_for_user(user_id=dto.user_id)
        if not stored_events:
            return []
        clock = await self.user_clock.get_user_clock(user_id=dto.user_id)
        now = self.now_provider()
        return [
            present_event(stored=stored, clock=clock, now=now)
            for stored in stored_events
        ]
