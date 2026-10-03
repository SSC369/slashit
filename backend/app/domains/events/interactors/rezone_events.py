"""FR-12, FR-13: after a timezone change, move the user's events and their
alerts to the new zone. Deferred by identity by name, as reminders' is."""

from collections.abc import Callable
from datetime import datetime
from uuid import UUID

from app.domains.events.interfaces.dtos import StoredEventDTO, UserClockDTO
from app.domains.events.interfaces.ports import UserClockPort
from app.domains.events.interfaces.repositories import EventRepository
from app.domains.events.services.alert_arming import EventAlertArming
from app.domains.events.services.schedule import resolve, rezone_schedule


class RezoneEventsInteractor:
    def __init__(
        self,
        *,
        event_repository: EventRepository,
        user_clock: UserClockPort,
        alert_arming: EventAlertArming,
        now_provider: Callable[[], datetime],
    ) -> None:
        self.event_repository = event_repository
        self.user_clock = user_clock
        self.alert_arming = alert_arming
        self.now_provider = now_provider

    async def rezone_events(self, *, user_id: UUID) -> int:
        """Move every live event not already in the user's zone, and re-arm
        its alerts, whose fire times follow (an all-day alert counts back from
        a local time). Safe to repeat: a moved event is skipped. Returns how
        many moved."""
        clock = await self.user_clock.get_user_clock(user_id=user_id)
        now = self.now_provider()
        events = await self.event_repository.list_for_user(user_id=user_id)
        moved = [
            stored
            for stored in events
            if stored.schedule.timezone != clock.timezone
            and await self._move_one(stored=stored, clock=clock, now=now)
        ]
        return len(moved)

    async def _move_one(
        self, *, stored: StoredEventDTO, clock: UserClockDTO, now: datetime
    ) -> bool:
        schedule = rezone_schedule(
            schedule=stored.schedule,
            resolved=resolve(schedule=stored.schedule, now=now),
            timezone=clock.timezone,
        )
        resolved = resolve(schedule=schedule, now=now)
        moved = await self.event_repository.move_occurrence(
            user_id=stored.user_id,
            event_id=stored.id,
            schedule=schedule,
            starts_at=resolved.starts_at,
            ends_at=resolved.ends_at,
        )
        if moved is None:
            return False
        if moved.alert_leads_minutes:
            await self.alert_arming.arm_alerts(
                stored=moved, clock=clock, origin="edit", now=now
            )
        else:
            await self.event_repository.finish_arming(
                user_id=moved.user_id, event_id=moved.id, leads=()
            )
        return True
