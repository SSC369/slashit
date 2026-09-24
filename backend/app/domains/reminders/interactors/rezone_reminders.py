"""AD-6: after a timezone change, move the user's live reminders to the new zone.

A repeating reminder keeps its clock time and days (FR-10). A one-time
reminder keeps its instant (FR-11); only its local date and time are read
again in the new zone. A pending snooze is an instant too, and is left alone.
"""

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

import structlog

from app.domains.reminders.constants import REZONE_MAX_PASSES
from app.domains.reminders.interfaces.dtos import ReminderDTO
from app.domains.reminders.interfaces.ports import UserClockPort
from app.domains.reminders.interfaces.repositories import (
    ReminderRepository,
    RezoneWrite,
)
from app.domains.reminders.services.schedule import RepeatKind, next_occurrence

logger = structlog.get_logger(__name__)


class RezoneRemindersInteractor:
    def __init__(
        self,
        *,
        reminder_repository: ReminderRepository,
        user_clock: UserClockPort,
        now_provider: Callable[[], datetime],
    ) -> None:
        self.reminder_repository = reminder_repository
        self.user_clock = user_clock
        self.now_provider = now_provider

    async def rezone_reminders(self, *, user_id: UUID) -> int:
        """Returns how many reminders moved. Reads the zone now, not when the
        change was queued, so after two quick changes the last one wins."""
        clock = await self.user_clock.get_user_clock(user_id=user_id)
        moved_count = 0
        for _ in range(REZONE_MAX_PASSES):
            stale = await self._list_stale(user_id=user_id, timezone=clock.timezone)
            if not stale:
                return moved_count
            for reminder in stale:
                moved_count += int(
                    await self._move(reminder=reminder, timezone=clock.timezone)
                )
        remaining = await self._list_stale(user_id=user_id, timezone=clock.timezone)
        if remaining:
            logger.warning(
                "reminders.rezone_incomplete",
                user_id=str(user_id),
                remaining_count=len(remaining),
            )
        return moved_count

    async def _list_stale(self, *, user_id: UUID, timezone: str) -> list[ReminderDTO]:
        reminders = await self.reminder_repository.list_for_user(
            user_id=user_id, search=None
        )
        return [
            reminder
            for reminder in reminders
            if reminder.state != "done" and reminder.schedule_timezone != timezone
        ]

    async def _move(self, *, reminder: ReminderDTO, timezone: str) -> bool:
        return await self.reminder_repository.rezone(
            user_id=reminder.user_id,
            reminder_id=reminder.id,
            expected_updated_at=reminder.updated_at,
            write=self._build_rezone_write(reminder=reminder, timezone=timezone),
        )

    def _build_rezone_write(
        self, *, reminder: ReminderDTO, timezone: str
    ) -> RezoneWrite:
        zone = ZoneInfo(timezone)
        spec = reminder.spec
        if spec.repeat_kind is RepeatKind.NONE:
            # FR-11: the instant stays; the words describing it move.
            instant = spec.one_time_at
            if instant is not None:
                local = instant.astimezone(zone)
                spec = replace(
                    spec,
                    local_time=local.time().replace(second=0, microsecond=0),
                    anchor_local_date=local.date(),
                )
            return RezoneWrite(
                spec=spec,
                schedule_timezone=timezone,
                next_fire_at=reminder.next_fire_at,
            )
        # FR-10: same clock time and days, counted from now in the new zone.
        return RezoneWrite(
            spec=spec,
            schedule_timezone=timezone,
            next_fire_at=next_occurrence(
                spec=spec, timezone=zone, after=self.now_provider()
            ),
        )
