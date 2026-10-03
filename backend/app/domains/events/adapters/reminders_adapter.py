"""Implements events' EventAlertsPort against the reminders domain.

Each alert is a one-time reminder row carrying the event's id (build plan
AD-3); reminders fires it through 003's pipeline. Reminders reports an alert
it did not set by its fire time; this adapter turns that back into the lead.
"""

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from app.domains.events.interfaces.dtos import (
    AlertNotSetDTO,
    EventAlertToSet,
    RecordOriginValue,
)
from app.domains.events.services.schedule import describe_alert
from app.domains.reminders.public import EventAlertRequest, ReminderService


class RemindersAlertsAdapter:
    def __init__(self, *, reminder_service: ReminderService) -> None:
        self.reminder_service = reminder_service

    async def set_alerts(
        self,
        *,
        user_id: UUID,
        event_id: UUID,
        title: str,
        alerts: Sequence[EventAlertToSet],
        origin: RecordOriginValue,
        now: datetime,
    ) -> list[AlertNotSetDTO]:
        lead_by_fire_time = {alert.fires_at: alert.lead_minutes for alert in alerts}
        not_set = await self.reminder_service.set_event_alerts(
            user_id=user_id,
            event_id=event_id,
            title=title,
            alerts=[
                EventAlertRequest(fires_at=alert.fires_at, detail=alert.detail)
                for alert in alerts
            ],
            origin=origin,
            now=now,
        )
        return [
            AlertNotSetDTO(
                lead_minutes=lead_by_fire_time[alert.fires_at],
                text=describe_alert(lead_minutes=lead_by_fire_time[alert.fires_at]),
                reason=alert.reason,
            )
            for alert in not_set
        ]

    async def clear_alerts(self, *, user_id: UUID, event_id: UUID) -> None:
        await self.reminder_service.clear_event_alerts(
            user_id=user_id, event_id=event_id
        )
