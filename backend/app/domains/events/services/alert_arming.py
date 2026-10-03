"""Arms an event's alerts and keeps its stored leads in step with them.

Shared by create, edit and the yearly roll, so each sets alerts the same way
(build plan AD-8). The event is written first and its alerts second, each in
its own transaction (4.2 Q1, dev log D-16): a failure between the two leaves
the event without alerts, which the 15-minute sweep repairs.
"""

from dataclasses import dataclass, replace
from datetime import datetime

import structlog

from app.domains.events.interfaces.dtos import (
    AlertNotSetDTO,
    EventAlertToSet,
    RecordOriginValue,
    StoredEventDTO,
    UserClockDTO,
)
from app.domains.events.interfaces.ports import EventAlertsPort
from app.domains.events.interfaces.repositories import EventRepository
from app.domains.events.services.schedule import (
    alert_fire_times,
    describe_alert_detail,
    resolve,
)

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class ArmedEvent:
    """The event as stored after arming, and the alerts that were not set."""

    stored: StoredEventDTO
    alerts_not_set: tuple[AlertNotSetDTO, ...]


class EventAlertArming:
    def __init__(
        self, *, alerts: EventAlertsPort, event_repository: EventRepository
    ) -> None:
        self.alerts = alerts
        self.event_repository = event_repository

    async def arm_alerts(
        self,
        *,
        stored: StoredEventDTO,
        clock: UserClockDTO,
        origin: RecordOriginValue,
        now: datetime,
    ) -> ArmedEvent:
        """Set one alert per stored lead for the next or only occurrence, then
        mark the event's alerts as no longer pending. A lead that was not set
        is dropped from the event (FR-19, FR-33), so the event only ever lists
        alerts that will fire. An outage leaves the event pending for the
        sweep to arm (dev log D-20), and reports nothing not set."""
        try:
            not_set = await self.alerts.set_alerts(
                user_id=stored.user_id,
                event_id=stored.id,
                title=stored.title,
                alerts=alerts_to_set(stored=stored, clock=clock, now=now),
                origin=origin,
                now=now,
            )
        except Exception:
            # Broad on purpose: the event is saved; the sweep sets its alerts.
            logger.exception("events.alerts_not_armed", event_id=str(stored.id))
            return ArmedEvent(stored=stored, alerts_not_set=())
        return await self._finish_arming(stored=stored, not_set=not_set)

    async def _finish_arming(
        self, *, stored: StoredEventDTO, not_set: list[AlertNotSetDTO]
    ) -> ArmedEvent:
        dropped = {alert.lead_minutes for alert in not_set}
        kept_leads = tuple(
            lead for lead in stored.alert_leads_minutes if lead not in dropped
        )
        await self.event_repository.finish_arming(
            user_id=stored.user_id, event_id=stored.id, leads=kept_leads
        )
        return ArmedEvent(
            stored=replace(stored, alert_leads_minutes=kept_leads),
            alerts_not_set=tuple(not_set),
        )


def alerts_to_set(
    *, stored: StoredEventDTO, clock: UserClockDTO, now: datetime
) -> list[EventAlertToSet]:
    """Each stored lead's fire time and notification line, soonest first."""
    resolved = resolve(schedule=stored.schedule, now=now)
    return [
        EventAlertToSet(
            lead_minutes=alert_time.lead_minutes,
            fires_at=alert_time.fires_at,
            detail=describe_alert_detail(
                schedule=stored.schedule,
                resolved=resolved,
                lead_minutes=alert_time.lead_minutes,
            ),
        )
        for alert_time in alert_fire_times(
            schedule=stored.schedule,
            resolved=resolved,
            leads=stored.alert_leads_minutes,
            default_reminder_time=clock.default_reminder_time,
        )
    ]
