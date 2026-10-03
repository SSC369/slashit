"""In-memory ports around the events domain: its clock and analytics, and
capture's and records' ports onto it."""

from collections.abc import Sequence
from datetime import datetime, time
from uuid import UUID

from app.domains.capture.interfaces.ports import ExtractionPort
from app.domains.capture.services.event_capture import EventCaptureService
from app.domains.events.interfaces.dtos import (
    AlertNotSetDTO,
    EventAlertToSet,
    RecordOriginValue,
    UserClockDTO,
)
from app.domains.events.interfaces.repositories import EventRepository
from app.domains.events.public import (
    EventDTO,
    EventFields,
    EventLimitReached,
    EventNeedsDate,
)
from app.domains.events.services.alert_arming import EventAlertArming
from app.domains.events.services.schedule import describe_alert

EventCreateOutcome = EventDTO | EventLimitReached | EventNeedsDate


class FakeEventUserClockPort:
    def __init__(
        self, *, timezone: str = "Asia/Kolkata", default_reminder_time: time = time(9)
    ) -> None:
        self.clock = UserClockDTO(
            timezone=timezone, default_reminder_time=default_reminder_time
        )

    async def get_user_clock(self, *, user_id: UUID) -> UserClockDTO:
        return self.clock


class FakeEventAnalyticsPort:
    def __init__(self) -> None:
        self.recorded: list[dict[str, bool]] = []

    async def record_event_created(
        self, *, user_id: UUID, field_presence: dict[str, bool]
    ) -> None:
        self.recorded.append(dict(field_presence))


class FakeEventPort:
    """Capture's EventPort. Returns ``outcome`` for every create, and keeps
    the fields it was given."""

    def __init__(
        self,
        *,
        outcome: EventCreateOutcome | None = None,
        upcoming: list[EventDTO] | None = None,
    ) -> None:
        self.outcome = outcome
        self.upcoming = list(upcoming or [])
        self.created_fields: list[EventFields] = []

    async def create_event(
        self, *, user_id: UUID, fields: EventFields, original_input: str
    ) -> EventCreateOutcome:
        self.created_fields.append(fields)
        assert self.outcome is not None
        return self.outcome

    async def list_upcoming(self, *, user_id: UUID) -> list[EventDTO]:
        return [event for event in self.upcoming if event.user_id == user_id]


class FakeEventRecordsPort:
    def __init__(self, *, events: list[EventDTO] | None = None) -> None:
        self.events = list(events or [])

    async def list_events(self, *, user_id: UUID) -> list[EventDTO]:
        return [event for event in self.events if event.user_id == user_id]


def fake_event_capture(
    *, extraction: ExtractionPort, event_port: FakeEventPort | None = None
) -> EventCaptureService:
    return EventCaptureService(
        event_port=event_port or FakeEventPort(), extraction=extraction
    )


class FakeEventAlertsPort:
    """Events' EventAlertsPort, behaving as reminders does: a fire time not
    after now is passed; past ``room`` alerts, the later ones are over the
    cap. Keeps every event's set alerts by id."""

    def __init__(self, *, room: int = 100, fail: bool = False) -> None:
        self.room = room
        self.fail = fail
        self.alerts_by_event: dict[UUID, list[EventAlertToSet]] = {}
        self.cleared: list[UUID] = []

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
        if self.fail:
            raise ConnectionError("reminders unavailable")
        soonest_first = sorted(alerts, key=lambda alert: alert.fires_at)
        upcoming = [alert for alert in soonest_first if alert.fires_at > now]
        self.alerts_by_event[event_id] = upcoming[: self.room]
        passed = [alert for alert in soonest_first if alert.fires_at <= now]
        return [_not_set(alert=alert, reason="passed") for alert in passed] + [
            _not_set(alert=alert, reason="cap") for alert in upcoming[self.room :]
        ]

    async def clear_alerts(self, *, user_id: UUID, event_id: UUID) -> None:
        self.cleared.append(event_id)
        self.alerts_by_event.pop(event_id, None)


def _not_set(*, alert: EventAlertToSet, reason: str) -> AlertNotSetDTO:
    return AlertNotSetDTO(
        lead_minutes=alert.lead_minutes,
        text=describe_alert(lead_minutes=alert.lead_minutes),
        reason="passed" if reason == "passed" else "cap",
    )


def fake_alert_arming(
    *, repository: EventRepository, alerts: FakeEventAlertsPort | None = None
) -> EventAlertArming:
    return EventAlertArming(
        alerts=alerts or FakeEventAlertsPort(), event_repository=repository
    )
