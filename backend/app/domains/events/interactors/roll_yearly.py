"""Build plan AD-4 and 4.2 Q1: the 15-minute sweep.

It moves each yearly event whose occurrence has ended to its next one and
re-arms every alert for it (FR-20), then arms any event whose alerts were
left pending by a failure between the event's write and its alerts' (dev log
D-16, D-20). Runs on the service role; each event is written in its own
user's transaction.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

import structlog

from app.domains.events.constants import ALERTS_PENDING_GRACE, ROLL_BATCH
from app.domains.events.interfaces.dtos import EventTargetDTO
from app.domains.events.interfaces.ports import UserClockPort
from app.domains.events.interfaces.repositories import EventRepository
from app.domains.events.services.alert_arming import EventAlertArming
from app.domains.events.services.schedule import resolve

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class SweepCounts:
    rolled: int
    repaired: int


class RollYearlyInteractor:
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

    async def roll_yearly(self) -> SweepCounts:
        """Roll, then repair. Each event is its own unit: one that fails is
        logged and left pending for the next sweep. Nothing raises."""
        now = self.now_provider()
        to_roll = await self.event_repository.select_yearly_to_roll(
            now=now, limit=ROLL_BATCH
        )
        rolled = [
            target for target in to_roll if await self._roll_one(target=target, now=now)
        ]
        pending = await self.event_repository.select_alerts_pending(
            updated_before=now - ALERTS_PENDING_GRACE, limit=ROLL_BATCH
        )
        repaired = [
            target for target in pending if await self._arm_one(target=target, now=now)
        ]
        return SweepCounts(rolled=len(rolled), repaired=len(repaired))

    async def _roll_one(self, *, target: EventTargetDTO, now: datetime) -> bool:
        stored = await self.event_repository.get_by_id(
            user_id=target.user_id, event_id=target.event_id
        )
        if stored is None:
            return False
        resolved = resolve(schedule=stored.schedule, now=now)
        moved = await self.event_repository.move_occurrence(
            user_id=target.user_id,
            event_id=target.event_id,
            schedule=stored.schedule,
            starts_at=resolved.starts_at,
            ends_at=resolved.ends_at,
        )
        if moved is None:
            return False
        return await self._arm_one(target=target, now=now)

    async def _arm_one(self, *, target: EventTargetDTO, now: datetime) -> bool:
        stored = await self.event_repository.get_by_id(
            user_id=target.user_id, event_id=target.event_id
        )
        if stored is None:
            return False
        clock = await self.user_clock.get_user_clock(user_id=target.user_id)
        armed = await self.alert_arming.arm_alerts(
            stored=stored, clock=clock, origin="command", now=now
        )
        if armed.alerts_not_set:
            # A lead longer than the time to next year's occurrence, or the
            # cap: counted, never named, since no one is looking (T6).
            logger.info(
                "events.alerts_not_set_on_sweep",
                event_id=str(target.event_id),
                not_set_count=len(armed.alerts_not_set),
            )
        return True
