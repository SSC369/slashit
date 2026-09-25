"""Fire one occurrence of one reminder (FR-12, FR-16 to FR-18, FR-23, FR-24).

Two steps, each safe to repeat. The firing and the reminder's new state are
written in one transaction; the notification is then published, which is a
no-op if it already was. A retry after a failure between the two finds the
firing already written and publishes again, so nothing is lost and nothing
is doubled (AD-3).
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

import structlog

from app.domains.reminders.interfaces.dtos import (
    FiringAnnouncement,
    FiringDTO,
    ReminderDTO,
)
from app.domains.reminders.interfaces.ports import NotificationPort
from app.domains.reminders.interfaces.repositories import (
    FiringWrite,
    ReminderRepository,
    ReminderStateWrite,
)
from app.domains.reminders.services.firing import classify_lateness, collapse_to_latest
from app.domains.reminders.services.schedule import RepeatKind, next_occurrence

logger = structlog.get_logger(__name__)

FiringOutcomeValue = Literal["fired", "already_fired", "skipped"]


@dataclass(frozen=True)
class _FiringPlan:
    firing: FiringWrite
    state: ReminderStateWrite


class FireOneInteractor:
    def __init__(
        self,
        *,
        reminder_repository: ReminderRepository,
        notifications: NotificationPort,
        now_provider: Callable[[], datetime],
    ) -> None:
        self.reminder_repository = reminder_repository
        self.notifications = notifications
        self.now_provider = now_provider

    async def fire_one(
        self, *, reminder_id: UUID, scheduled_for: datetime
    ) -> FiringOutcomeValue:
        now = self.now_provider()
        reminder = await self.reminder_repository.get_for_firing(
            reminder_id=reminder_id
        )
        if reminder is None or reminder.next_due_at != scheduled_for:
            await self._finish_interrupted_firing(
                reminder=reminder, scheduled_for=scheduled_for
            )
            logger.info("reminder.fire_skipped", reminder_id=str(reminder_id))
            return "skipped"

        plan = self._plan_firing(
            reminder=reminder, scheduled_for=scheduled_for, now=now
        )
        recorded = await self.reminder_repository.record_firing(
            user_id=reminder.user_id,
            reminder_id=reminder.id,
            expected_due_at=scheduled_for,
            firing=plan.firing,
            state=plan.state,
        )
        if recorded is None:
            logger.info("reminder.fire_skipped", reminder_id=str(reminder_id))
            return "skipped"

        await self._announce(reminder=reminder, firing=recorded.firing)
        self._log_fired(firing=recorded.firing, is_new=recorded.is_new)
        return "fired" if recorded.is_new else "already_fired"

    def _plan_firing(
        self, *, reminder: ReminderDTO, scheduled_for: datetime, now: datetime
    ) -> _FiringPlan:
        timezone = ZoneInfo(reminder.schedule_timezone)
        is_snooze = reminder.snoozed_until == scheduled_for
        is_one_time = reminder.spec.repeat_kind is RepeatKind.NONE
        occurrence = scheduled_for
        if not is_snooze and not is_one_time:
            occurrence = collapse_to_latest(
                spec=reminder.spec,
                timezone=timezone,
                scheduled_for=scheduled_for,
                now=now,
            )
        lateness = classify_lateness(scheduled_for=occurrence, fired_at=now)
        return _FiringPlan(
            firing=FiringWrite(
                scheduled_for=occurrence, fired_at=now, lateness=lateness
            ),
            state=ReminderStateWrite(
                state="fired",
                next_fire_at=self._next_series_instant(
                    reminder=reminder,
                    is_snooze=is_snooze,
                    occurrence=occurrence,
                    now=now,
                ),
                snoozed_until=None if is_snooze else reminder.snoozed_until,
                last_fired_at=occurrence,
                last_action="missed" if lateness == "missed" else None,
            ),
        )

    def _next_series_instant(
        self,
        *,
        reminder: ReminderDTO,
        is_snooze: bool,
        occurrence: datetime,
        now: datetime,
    ) -> datetime | None:
        """FR-24: the series moves on at firing, whatever the user later does.
        A snooze firing leaves the series where it was (4.2 decision 1)."""
        if is_snooze:
            return reminder.next_fire_at
        if reminder.spec.repeat_kind is RepeatKind.NONE:
            return None
        return next_occurrence(
            spec=reminder.spec,
            timezone=ZoneInfo(reminder.schedule_timezone),
            after=max(now, occurrence),
        )

    async def _finish_interrupted_firing(
        self, *, reminder: ReminderDTO | None, scheduled_for: datetime
    ) -> None:
        """A retry whose first run wrote the firing but died before the
        notification: the reminder has already moved on, so find that firing
        and publish it. Publishing twice is a no-op."""
        if reminder is None:
            return
        firing = await self.reminder_repository.get_latest_firing(
            user_id=reminder.user_id, reminder_id=reminder.id
        )
        if firing is not None and firing.fired_at >= scheduled_for:
            await self._announce(reminder=reminder, firing=firing)

    async def _announce(self, *, reminder: ReminderDTO, firing: FiringDTO) -> None:
        is_repeating = reminder.spec.repeat_kind is not RepeatKind.NONE
        await self.notifications.announce_firing(
            announcement=FiringAnnouncement(
                user_id=reminder.user_id,
                firing_id=firing.id,
                reminder_id=reminder.id,
                title=reminder.description,
                detail=reminder.summary.repeat_text if is_repeating else "",
                lateness=firing.lateness,
                occurred_at=firing.scheduled_for,
                time_zone=reminder.schedule_timezone,
            )
        )

    def _log_fired(self, *, firing: FiringDTO, is_new: bool) -> None:
        """NFR-1 is read from ``delay_ms``. Never the reminder's text (T6)."""
        delay_ms = int((firing.fired_at - firing.scheduled_for).total_seconds() * 1000)
        logger.info(
            "reminder.fired" if is_new else "reminder.fire_repeated",
            reminder_id=str(firing.reminder_id),
            firing_id=str(firing.id),
            lateness=firing.lateness,
            delay_ms=delay_ms,
        )
