"""Epic 007, sub-plan 4.2, T-2.5: edit and delete an event.

C-8 (alerts move by their own leads; a text edit leaves them), C-9 (add,
change, remove alerts), C-10 (delete takes the alerts, alerts first) and
C-15 (an edit to a 501st upcoming event is refused), with the form's rules.
"""

import uuid
from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

import pytest

from app.domains.events.graphql.errors import (
    EventField,
    EventInvalidError,
    EventInvalidReason,
    EventNotFoundError,
)
from app.domains.events.interactors.create_event import CreateEventInteractor
from app.domains.events.interactors.delete_event import DeleteEventInteractor
from app.domains.events.interactors.dtos import (
    CreateEventInputDTO,
    DeleteEventInputDTO,
    UpdateEventInputDTO,
)
from app.domains.events.interactors.update_event import UpdateEventInteractor
from app.domains.events.interfaces.dtos import EventDTO, EventEdit, EventFields
from app.domains.events.services.alert_arming import EventAlertArming
from tests.fakes.fake_calendar_event_repository import FakeCalendarEventRepository
from tests.fakes.fake_event_ports import (
    FakeEventAlertsPort,
    FakeEventAnalyticsPort,
    FakeEventUserClockPort,
    fake_alert_arming,
)

KOLKATA = ZoneInfo("Asia/Kolkata")
USER = uuid.uuid4()
OTHER_USER = uuid.uuid4()
# Friday 2 October 2026, 10:00 in Kolkata.
NOW = datetime(2026, 10, 2, 10, 0, tzinfo=KOLKATA).astimezone(UTC)


class World:
    def __init__(self) -> None:
        self.repository = FakeCalendarEventRepository()
        self.alerts = FakeEventAlertsPort()
        self.clock = FakeEventUserClockPort()

    async def create(
        self,
        *,
        leads: tuple[int, ...] = (1440, 60),
        start_date: date = date(2026, 10, 9),
        user_id: uuid.UUID = USER,
    ) -> EventDTO:
        event = await CreateEventInteractor(
            event_repository=self.repository,
            user_clock=self.clock,
            alert_arming=self._arming(),
            analytics=FakeEventAnalyticsPort(),
            now_provider=lambda: NOW,
        ).create_event(
            dto=CreateEventInputDTO(
                user_id=user_id,
                fields=EventFields(
                    title="Dentist",
                    start_date=start_date,
                    has_year=True,
                    start_time=time(16),
                    end_date=None,
                    end_time=time(17),
                    location="Apollo Clinic",
                    description=None,
                    repeat_yearly=False,
                    alert_leads_minutes=leads,
                ),
                origin="command",
                original_input="/add-event Dentist",
            )
        )
        assert isinstance(event, EventDTO)
        return event

    def updater(self) -> UpdateEventInteractor:
        return UpdateEventInteractor(
            event_repository=self.repository,
            user_clock=self.clock,
            alert_arming=self._arming(),
            now_provider=lambda: NOW,
        )

    def deleter(self) -> DeleteEventInteractor:
        return DeleteEventInteractor(
            event_repository=self.repository, alerts=self.alerts
        )

    def alert_times(self, *, event_id: uuid.UUID) -> list[datetime]:
        return [alert.fires_at for alert in self.alerts.alerts_by_event[event_id]]

    def _arming(self) -> EventAlertArming:
        return fake_alert_arming(repository=self.repository, alerts=self.alerts)


def _edit(
    *,
    title: str = "Dentist",
    location: str | None = "Apollo Clinic",
    description: str | None = None,
    start_date: date = date(2026, 10, 9),
    start_time: time | None = time(16),
    end_date: date | None = None,
    end_time: time | None = time(17),
    leads: tuple[int, ...] = (1440, 60),
) -> EventEdit:
    return EventEdit(
        title=title,
        location=location,
        description=description,
        start_date=start_date,
        start_time=start_time,
        end_date=end_date,
        end_time=end_time,
        repeat_yearly=False,
        alert_leads_minutes=leads,
    )


def _at(day: int, hour: int) -> datetime:
    return datetime(2026, 10, day, hour, tzinfo=KOLKATA)


async def test_moving_the_event_moves_every_alert_by_its_own_lead() -> None:
    """C-8, FR-21."""
    world = World()
    event = await world.create()

    updated = await world.updater().update_event(
        dto=UpdateEventInputDTO(
            user_id=USER, event_id=event.id, edit=_edit(start_date=date(2026, 10, 12))
        )
    )

    assert world.alert_times(event_id=event.id) == [_at(11, 16), _at(12, 15)]
    assert [alert.fires_at for alert in updated.event.alerts] == [
        _at(11, 16),
        _at(12, 15),
    ]


async def test_a_location_edit_leaves_the_alerts_alone() -> None:
    """C-8: only title, schedule and leads touch the alert rows."""
    world = World()
    event = await world.create()
    world.alerts.alerts_by_event[event.id] = []

    await world.updater().update_event(
        dto=UpdateEventInputDTO(
            user_id=USER, event_id=event.id, edit=_edit(location="Indiranagar")
        )
    )

    assert world.alert_times(event_id=event.id) == []


async def test_the_form_adds_changes_and_removes_alerts() -> None:
    """C-9, FR-22 and FR-34: the list sent is the list kept, each once."""
    world = World()
    event = await world.create(leads=(1440,))

    updated = await world.updater().update_event(
        dto=UpdateEventInputDTO(
            user_id=USER, event_id=event.id, edit=_edit(leads=(60, 15, 60))
        )
    )

    assert [alert.text for alert in updated.event.alerts] == [
        "1 hour before",
        "15 minutes before",
    ]
    assert world.repository.rows[0].alert_leads_minutes == (15, 60)


async def test_a_passed_alert_in_the_form_is_named_and_dropped() -> None:
    """FR-19 on edit, as `EventEditAlertPast` draws it."""
    world = World()
    event = await world.create(leads=(60,))

    updated = await world.updater().update_event(
        dto=UpdateEventInputDTO(
            user_id=USER, event_id=event.id, edit=_edit(leads=(11520, 60))
        )
    )

    assert [alert.text for alert in updated.alerts_not_set] == ["8 days before"]
    assert world.repository.rows[0].alert_leads_minutes == (60,)


@pytest.mark.parametrize(
    ("edit", "field", "reason"),
    [
        (_edit(title="  "), EventField.TITLE, EventInvalidReason.EMPTY),
        (_edit(title="x" * 201), EventField.TITLE, EventInvalidReason.TOO_LONG),
        (
            _edit(end_date=date(2026, 10, 8)),
            EventField.END,
            EventInvalidReason.END_BEFORE_START,
        ),
        (
            _edit(start_time=None, end_time=time(17)),
            EventField.END,
            EventInvalidReason.END_BEFORE_START,
        ),
    ],
)
async def test_the_form_rules_refuse_and_change_nothing(
    edit: EventEdit, field: EventField, reason: EventInvalidReason
) -> None:
    """FR-28 and `EventEditInvalid`."""
    world = World()
    event = await world.create()

    with pytest.raises(EventInvalidError) as raised:
        await world.updater().update_event(
            dto=UpdateEventInputDTO(user_id=USER, event_id=event.id, edit=edit)
        )

    assert (raised.value.field, raised.value.reason) == (field, reason)
    assert world.repository.rows[0].title == "Dentist"


async def test_an_edit_to_a_501st_upcoming_event_is_refused() -> None:
    """C-15, FR-31: a past event moved into the future at the cap."""
    world = World()
    past = await world.create(start_date=date(2026, 9, 1), leads=())
    for _ in range(500):
        await world.create(leads=())

    with pytest.raises(EventInvalidError) as raised:
        await world.updater().update_event(
            dto=UpdateEventInputDTO(
                user_id=USER,
                event_id=past.id,
                edit=_edit(start_date=date(2026, 10, 20), leads=()),
            )
        )

    assert raised.value.reason is EventInvalidReason.LIMIT


async def test_another_users_event_cannot_be_edited_or_deleted() -> None:
    """NFR-6 and T7."""
    world = World()
    event = await world.create()

    with pytest.raises(EventNotFoundError):
        await world.updater().update_event(
            dto=UpdateEventInputDTO(user_id=OTHER_USER, event_id=event.id, edit=_edit())
        )
    with pytest.raises(EventNotFoundError):
        await world.deleter().delete_event(
            dto=DeleteEventInputDTO(user_id=OTHER_USER, event_id=event.id)
        )
    assert world.alerts.cleared == []


async def test_deleting_takes_every_alert_first() -> None:
    """C-10, FR-23, FR-29 and 4.2 Q1: alerts cleared, then the event."""
    world = World()
    event = await world.create()

    await world.deleter().delete_event(
        dto=DeleteEventInputDTO(user_id=USER, event_id=event.id)
    )

    assert world.alerts.cleared == [event.id]
    assert event.id not in world.alerts.alerts_by_event
    assert await world.repository.get_by_id(user_id=USER, event_id=event.id) is None
