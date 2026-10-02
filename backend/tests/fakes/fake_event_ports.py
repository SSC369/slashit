"""In-memory ports around the events domain: its clock and analytics, and
capture's and records' ports onto it."""

from datetime import time
from uuid import UUID

from app.domains.capture.interfaces.ports import ExtractionPort
from app.domains.capture.services.event_capture import EventCaptureService
from app.domains.events.interfaces.dtos import UserClockDTO
from app.domains.events.public import (
    EventDTO,
    EventFields,
    EventLimitReached,
    EventNeedsAlertChoice,
    EventNeedsDate,
)

EventCreateOutcome = (
    EventDTO | EventLimitReached | EventNeedsDate | EventNeedsAlertChoice
)


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
