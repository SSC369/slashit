"""Epic 007, sub-plan 4.1 §7: creating and listing events."""

import asyncio
import uuid
from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

import pytest

from app.domains.events.constants import MAX_UPCOMING_EVENTS
from app.domains.events.graphql.errors import EventNotFoundError
from app.domains.events.interactors.create_event import CreateEventInteractor
from app.domains.events.interactors.dtos import (
    CreateEventInputDTO,
    GetEventInputDTO,
    ListEventsInputDTO,
)
from app.domains.events.interactors.get_event import GetEventInteractor
from app.domains.events.interactors.list_events import ListEventsInteractor
from app.domains.events.interfaces.dtos import (
    AlertNotSetDTO,
    EventDTO,
    EventFields,
    EventLimitReached,
    EventNeedsDate,
)
from app.domains.events.services.schedule import EventStatus
from tests.fakes.fake_calendar_event_repository import FakeCalendarEventRepository
from tests.fakes.fake_event_ports import (
    FakeEventAlertsPort,
    FakeEventAnalyticsPort,
    FakeEventUserClockPort,
    fake_alert_arming,
)

USER = uuid.uuid4()
OTHER_USER = uuid.uuid4()
NOW = datetime(2026, 10, 2, 10, 0, tzinfo=ZoneInfo("Asia/Kolkata")).astimezone(UTC)


def _fields(
    *,
    title: str = "Dentist",
    start_date: date | None = date(2026, 10, 9),
    has_year: bool = False,
    start_time: time | None = time(16),
    end_time: time | None = None,
    location: str | None = None,
    repeat_yearly: bool = False,
    alert_leads_minutes: tuple[int, ...] = (),
) -> EventFields:
    return EventFields(
        title=title,
        start_date=start_date,
        has_year=has_year,
        start_time=start_time,
        end_date=None,
        end_time=end_time,
        location=location,
        description=None,
        repeat_yearly=repeat_yearly,
        alert_leads_minutes=alert_leads_minutes,
    )


def _interactors(
    repository: FakeCalendarEventRepository,
    *,
    alerts: FakeEventAlertsPort | None = None,
) -> tuple[CreateEventInteractor, ListEventsInteractor, FakeEventAnalyticsPort]:
    clock = FakeEventUserClockPort()
    analytics = FakeEventAnalyticsPort()
    create = CreateEventInteractor(
        event_repository=repository,
        user_clock=clock,
        alert_arming=fake_alert_arming(repository=repository, alerts=alerts),
        analytics=analytics,
        now_provider=lambda: NOW,
    )
    listing = ListEventsInteractor(
        event_repository=repository, user_clock=clock, now_provider=lambda: NOW
    )
    return create, listing, analytics


async def _create(
    interactor: CreateEventInteractor, fields: EventFields, *, user_id: uuid.UUID = USER
) -> object:
    return await interactor.create_event(
        dto=CreateEventInputDTO(
            user_id=user_id,
            fields=fields,
            origin="command",
            original_input="/add-event",
        )
    )


async def test_an_event_is_saved_with_its_words_and_one_alert() -> None:
    """FR-1, FR-8, FR-14."""
    repository = FakeCalendarEventRepository()
    create, _, analytics = _interactors(repository)
    event = await _create(
        create,
        _fields(end_time=time(17), location="Apollo Clinic", alert_leads_minutes=(60,)),
    )
    assert isinstance(event, EventDTO)
    assert event.when_text == "Fri 9 Oct, 4:00 to 5:00 PM"
    assert event.alert_text == "1 hour before"
    assert event.location == "Apollo Clinic"
    assert event.status == EventStatus.UPCOMING
    assert analytics.recorded == [
        {
            "all_day": False,
            "has_end": True,
            "has_location": True,
            "yearly": False,
            "has_alert": True,
        }
    ]


async def test_no_date_asks_and_writes_nothing() -> None:
    """FR-2."""
    repository = FakeCalendarEventRepository()
    create, _, _ = _interactors(repository)
    outcome = await _create(create, _fields(start_date=None))
    assert outcome == EventNeedsDate(title="Dentist")
    assert repository.rows == []


async def test_every_alert_said_is_set_soonest_first() -> None:
    """4.2 C-1, FR-14: "remind me 1 week before and 1 day before" sets both."""
    repository = FakeCalendarEventRepository()
    alerts = FakeEventAlertsPort()
    create, _, _ = _interactors(repository, alerts=alerts)

    event = await _create(create, _fields(alert_leads_minutes=(1440, 10080)))

    assert isinstance(event, EventDTO)
    assert [alert.text for alert in event.alerts] == ["1 week before", "1 day before"]
    assert [alert.fires_at for alert in event.alerts] == [
        datetime(2026, 10, 2, 16, tzinfo=ZoneInfo("Asia/Kolkata")),
        datetime(2026, 10, 8, 16, tzinfo=ZoneInfo("Asia/Kolkata")),
    ]
    assert event.alerts_not_set == ()
    assert repository.rows[0].alert_leads_minutes == (1440, 10080)
    assert [alert.detail for alert in alerts.alerts_by_event[event.id]] == [
        "1 week before · Fri 9 Oct, 4:00 PM",
        "1 day before · Fri 9 Oct, 4:00 PM",
    ]


async def test_the_same_alert_said_twice_is_one_alert_and_says_so() -> None:
    """4.2 C-2, FR-34."""
    repository = FakeCalendarEventRepository()
    create, _, _ = _interactors(repository)
    event = await _create(create, _fields(alert_leads_minutes=(1440, 120, 1440)))
    assert isinstance(event, EventDTO)
    assert [alert.lead_minutes for alert in event.alerts] == [1440, 120]
    assert event.alert_notes == ("“1 day before” was named twice, kept once",)
    assert repository.rows[0].alert_leads_minutes == (120, 1440)


async def test_a_passed_alert_is_named_and_dropped_and_the_rest_set() -> None:
    """4.2 C-4, FR-19: eight days before 9 Oct, 4 PM, has passed at 2 Oct, 10 AM."""
    repository = FakeCalendarEventRepository()
    create, _, _ = _interactors(repository)

    event = await _create(create, _fields(alert_leads_minutes=(11520, 60)))

    assert isinstance(event, EventDTO)
    assert event.alerts_not_set == (
        AlertNotSetDTO(lead_minutes=11520, text="8 days before", reason="passed"),
    )
    assert [alert.text for alert in event.alerts] == ["1 hour before"]
    assert repository.rows[0].alert_leads_minutes == (60,)


async def test_over_the_cap_the_soonest_firing_alerts_are_kept() -> None:
    """FR-33 and AD-8, as events sees it: the later alert is named."""
    repository = FakeCalendarEventRepository()
    create, _, _ = _interactors(repository, alerts=FakeEventAlertsPort(room=1))

    event = await _create(create, _fields(alert_leads_minutes=(1440, 60)))

    assert isinstance(event, EventDTO)
    assert event.alerts_not_set == (
        AlertNotSetDTO(lead_minutes=60, text="1 hour before", reason="cap"),
    )
    assert repository.rows[0].alert_leads_minutes == (1440,)


async def test_an_alerts_outage_saves_the_event_with_its_leads() -> None:
    """4.2 Q1: the event stands; the sweep sets its alerts later (D-16)."""
    repository = FakeCalendarEventRepository()
    create, _, _ = _interactors(repository, alerts=FakeEventAlertsPort(fail=True))

    event = await _create(create, _fields(alert_leads_minutes=(60,)))

    assert isinstance(event, EventDTO)
    assert event.alerts_not_set == ()
    assert repository.rows[0].alert_leads_minutes == (60,)


async def test_a_birthday_title_is_echoed_as_the_reason_for_yearly() -> None:
    """FR-9."""
    create, _, _ = _interactors(FakeCalendarEventRepository())
    event = await _create(
        create,
        _fields(
            title="Mom's birthday",
            start_date=date(2026, 10, 12),
            start_time=None,
            repeat_yearly=True,
        ),
    )
    assert isinstance(event, EventDTO)
    assert "Read from “birthday”" in event.when_notes
    assert "No time given, so all day" in event.when_notes


async def test_the_501st_upcoming_event_is_refused_and_past_ones_do_not_count() -> None:
    """FR-31."""
    repository = FakeCalendarEventRepository()
    create, _, _ = _interactors(repository)
    past = await _create(
        create, _fields(start_date=date(2019, 6, 14), has_year=True, start_time=None)
    )
    assert isinstance(past, EventDTO)
    for _ in range(MAX_UPCOMING_EVENTS):
        assert isinstance(await _create(create, _fields()), EventDTO)
    refused = await _create(create, _fields())
    assert refused == EventLimitReached(limit=MAX_UPCOMING_EVENTS)
    assert len(repository.rows) == MAX_UPCOMING_EVENTS + 1


async def test_events_list_upcoming_soonest_first_and_records_add_past_last() -> None:
    """FR-24, FR-25."""
    repository = FakeCalendarEventRepository()
    create, listing, _ = _interactors(repository)
    for fields in (
        _fields(title="Goa trip", start_date=date(2026, 12, 20), start_time=None),
        _fields(title="Dentist"),
        _fields(title="Graduation", start_date=date(2019, 6, 14), has_year=True),
        _fields(title="Housewarming", start_date=date(2026, 9, 26), has_year=True),
    ):
        await _create(create, fields)
    upcoming = await listing.list_upcoming(dto=ListEventsInputDTO(user_id=USER))
    assert [event.title for event in upcoming] == ["Dentist", "Goa trip"]
    every = await listing.list_for_records(dto=ListEventsInputDTO(user_id=USER))
    assert [event.title for event in every] == [
        "Dentist",
        "Goa trip",
        "Housewarming",
        "Graduation",
    ]


async def test_another_users_event_is_not_found() -> None:
    """NFR-6."""
    repository = FakeCalendarEventRepository()
    create, listing, _ = _interactors(repository)
    event = await _create(create, _fields(), user_id=OTHER_USER)
    assert isinstance(event, EventDTO)
    getter = GetEventInteractor(
        event_repository=repository,
        user_clock=FakeEventUserClockPort(),
        now_provider=lambda: NOW,
    )
    with pytest.raises(EventNotFoundError):
        await getter.get_event(dto=GetEventInputDTO(user_id=USER, event_id=event.id))
    assert await listing.list_for_records(dto=ListEventsInputDTO(user_id=USER)) == []


async def test_concurrent_creates_at_the_cap_give_one_success() -> None:
    """FR-31's race, against the fake's single-threaded count. The database
    serialises with an advisory lock; see the integration test."""
    repository = FakeCalendarEventRepository()
    create, _, _ = _interactors(repository)
    for _ in range(MAX_UPCOMING_EVENTS - 1):
        await _create(create, _fields())
    outcomes = await asyncio.gather(
        _create(create, _fields()), _create(create, _fields())
    )
    assert sum(isinstance(outcome, EventDTO) for outcome in outcomes) == 1
