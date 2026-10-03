"""Epic 007 FR-14, FR-19, FR-21, FR-33: set an event's alerts as one set.

Each alert is a one-time reminder row carrying the event's id (build plan
AD-3), so 003's firing, delivery and cap apply unchanged. The set replaces
whatever the event had, in one transaction (AD-8).
"""

from dataclasses import dataclass
from zoneinfo import ZoneInfo

from app.domains.reminders.constants import MAX_ACTIVE_REMINDERS
from app.domains.reminders.interactors.dtos import SetEventAlertsInputDTO
from app.domains.reminders.interfaces.dtos import AlertNotSet, EventAlertRequest
from app.domains.reminders.interfaces.ports import UserClockPort
from app.domains.reminders.interfaces.repositories import (
    EventAlertWrite,
    ReminderRepository,
)
from app.domains.reminders.services.schedule import RepeatKind, ScheduleSpec


@dataclass(frozen=True)
class _SortedAlerts:
    to_set: tuple[EventAlertRequest, ...]
    not_set: tuple[AlertNotSet, ...]


class SetEventAlertsInteractor:
    def __init__(
        self,
        *,
        reminder_repository: ReminderRepository,
        user_clock: UserClockPort,
    ) -> None:
        self.reminder_repository = reminder_repository
        self.user_clock = user_clock

    async def set_event_alerts(
        self, *, dto: SetEventAlertsInputDTO
    ) -> list[AlertNotSet]:
        """Store every alert that can fire, soonest first until the user holds
        100 active reminders, and report the rest. An empty ``alerts`` clears
        the event's alerts. Nothing raises: an alert not set is an outcome.
        """
        active_count = (
            await self.reminder_repository.count_active_for_user_outside_event(
                user_id=dto.user_id, event_id=dto.event_id
            )
        )
        sorted_alerts = _sort_alerts(dto=dto, active_count=active_count)
        clock = await self.user_clock.get_user_clock(user_id=dto.user_id)
        await self.reminder_repository.replace_event_alerts(
            user_id=dto.user_id,
            event_id=dto.event_id,
            writes=[
                _alert_write(title=dto.title, alert=alert, timezone=clock.timezone)
                for alert in sorted_alerts.to_set
            ],
            origin=dto.origin,
        )
        return list(sorted_alerts.not_set)


def _sort_alerts(*, dto: SetEventAlertsInputDTO, active_count: int) -> _SortedAlerts:
    """FR-19: a fire time not after now is passed. FR-33: of the rest, the
    soonest fill the room under the cap; the later ones are over it."""
    soonest_first = sorted(dto.alerts, key=lambda alert: alert.fires_at)
    passed = [alert for alert in soonest_first if alert.fires_at <= dto.now]
    upcoming = [alert for alert in soonest_first if alert.fires_at > dto.now]
    room = max(0, MAX_ACTIVE_REMINDERS - active_count)
    return _SortedAlerts(
        to_set=tuple(upcoming[:room]),
        not_set=tuple(
            [AlertNotSet(fires_at=alert.fires_at, reason="passed") for alert in passed]
            + [
                AlertNotSet(fires_at=alert.fires_at, reason="cap")
                for alert in upcoming[room:]
            ]
        ),
    )


def _alert_write(
    *, title: str, alert: EventAlertRequest, timezone: str
) -> EventAlertWrite:
    local_fire = alert.fires_at.astimezone(ZoneInfo(timezone))
    return EventAlertWrite(
        title=title,
        spec=ScheduleSpec(
            repeat_kind=RepeatKind.NONE,
            repeat_interval=1,
            repeat_weekdays=(),
            repeat_month_day=None,
            local_time=local_fire.time().replace(second=0, microsecond=0),
            anchor_local_date=local_fire.date(),
            one_time_at=alert.fires_at,
        ),
        schedule_timezone=timezone,
        detail=alert.detail,
    )
