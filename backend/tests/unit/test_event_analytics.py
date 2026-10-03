"""Epic 007, sub-plan 4.2, T-2.8: PRD §8's events, and C-19, T6: counts and
booleans only, never an event's words."""

import uuid
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.domains.events.interactors.create_event import CreateEventInteractor
from app.domains.events.interactors.dtos import CreateEventInputDTO, UpdateEventInputDTO
from app.domains.events.interactors.update_event import UpdateEventInteractor
from app.domains.events.interfaces.dtos import EventDTO, EventEdit, EventFields
from tests.fakes.fake_calendar_event_repository import FakeCalendarEventRepository
from tests.fakes.fake_event_ports import (
    FakeEventAlertsPort,
    FakeEventAnalyticsPort,
    FakeEventEmbedQueue,
    FakeEventUserClockPort,
    fake_alert_arming,
)

USER = uuid.uuid4()
NOW = datetime(2026, 10, 2, 10, 0, tzinfo=ZoneInfo("Asia/Kolkata")).astimezone(UTC)


class World:
    def __init__(self) -> None:
        self.repository = FakeCalendarEventRepository()
        self.analytics = FakeEventAnalyticsPort()
        self.alerts = FakeEventAlertsPort(room=1)
        self.clock = FakeEventUserClockPort()

    async def create(self) -> EventDTO:
        event = await CreateEventInteractor(
            event_repository=self.repository,
            user_clock=self.clock,
            alert_arming=fake_alert_arming(
                repository=self.repository, alerts=self.alerts
            ),
            analytics=self.analytics,
            embed_queue=FakeEventEmbedQueue(),
            now_provider=lambda: NOW,
        ).create_event(
            dto=CreateEventInputDTO(
                user_id=USER,
                fields=EventFields(
                    title="Secret surgery",
                    start_date=date(2026, 10, 9),
                    has_year=True,
                    start_time=time(16),
                    end_date=None,
                    end_time=None,
                    location="Apollo Clinic",
                    description=None,
                    repeat_yearly=False,
                    alert_leads_minutes=(11520, 1440, 60),
                ),
                origin="command",
                original_input="/add-event Secret surgery",
            )
        )
        assert isinstance(event, EventDTO)
        return event


async def test_create_records_the_alert_count_and_each_alert_not_set() -> None:
    """PRD §8 "alerts per event"; FR-19 and FR-33 per alert."""
    world = World()
    await world.create()

    assert world.analytics.alert_counts == [1]
    assert world.analytics.alerts_not_set == [(11520, False), (60, True)]


async def test_an_edit_records_what_changed_and_how_soon() -> None:
    """G2: edited within five minutes is read from minutes_since_created."""
    world = World()
    event = await world.create()
    stored = world.repository.rows[0]

    await UpdateEventInteractor(
        event_repository=world.repository,
        user_clock=world.clock,
        alert_arming=fake_alert_arming(
            repository=world.repository, alerts=world.alerts
        ),
        embed_queue=FakeEventEmbedQueue(),
        analytics=world.analytics,
        now_provider=lambda: stored.created_at + timedelta(minutes=3),
    ).update_event(
        dto=UpdateEventInputDTO(
            user_id=USER,
            event_id=event.id,
            edit=EventEdit(
                title="Secret surgery",
                location="Indiranagar",
                description=None,
                start_date=date(2026, 10, 9),
                start_time=time(16),
                end_date=None,
                end_time=None,
                repeat_yearly=False,
                alert_leads_minutes=(1440,),
            ),
        )
    )

    [edit] = world.analytics.edits
    assert edit == {
        "title_changed": False,
        "schedule_changed": False,
        "location_changed": True,
        "description_changed": False,
        "alerts_changed": False,
        "minutes_since_created": 3,
    }


async def test_no_property_carries_an_events_words() -> None:
    """C-19, T6: every value is a count or a boolean."""
    world = World()
    await world.create()

    values = [
        value for recorded in world.analytics.recorded for value in recorded.values()
    ] + [value for edit in world.analytics.edits for value in edit.values()]
    assert all(isinstance(value, bool | int) for value in values)
