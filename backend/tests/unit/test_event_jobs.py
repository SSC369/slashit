"""Epic 007, sub-plan 4.2, T-2.6: the 15-minute sweep, the nightly count and
the timezone move, with in-memory fakes.

C-11 (a yearly event rolls on and re-arms every alert; Feb 29), C-12 (the
sweep arms an event left pending), C-13 (the nightly count) and C-14 (a
timezone change across the date line).
"""

import uuid
from dataclasses import replace
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.domains.events.interactors.create_event import CreateEventInteractor
from app.domains.events.interactors.dtos import CreateEventInputDTO
from app.domains.events.interactors.reconcile_alerts import ReconcileAlertsInteractor
from app.domains.events.interactors.rezone_events import RezoneEventsInteractor
from app.domains.events.interactors.roll_yearly import RollYearlyInteractor
from app.domains.events.interfaces.dtos import EventDTO, EventFields, StoredEventDTO
from tests.fakes.fake_calendar_event_repository import FakeCalendarEventRepository
from tests.fakes.fake_event_ports import (
    FakeEventAlertsPort,
    FakeEventAnalyticsPort,
    FakeEventEmbedQueue,
    FakeEventUserClockPort,
    fake_alert_arming,
)

KOLKATA = ZoneInfo("Asia/Kolkata")
USER = uuid.uuid4()
# Friday 2 October 2026, 10:00 in Kolkata.
NOW = datetime(2026, 10, 2, 10, 0, tzinfo=KOLKATA).astimezone(UTC)


class World:
    def __init__(self, *, timezone: str = "Asia/Kolkata") -> None:
        self.repository = FakeCalendarEventRepository()
        self.alerts = FakeEventAlertsPort()
        self.clock = FakeEventUserClockPort(timezone=timezone)

    async def create(
        self,
        *,
        title: str = "Mom's birthday",
        start_date: date,
        start_time: time | None = None,
        repeat_yearly: bool = True,
        leads: tuple[int, ...] = (1440,),
    ) -> EventDTO:
        event = await CreateEventInteractor(
            event_repository=self.repository,
            user_clock=self.clock,
            alert_arming=fake_alert_arming(
                repository=self.repository, alerts=self.alerts
            ),
            analytics=FakeEventAnalyticsPort(),
            embed_queue=FakeEventEmbedQueue(),
            now_provider=lambda: NOW,
        ).create_event(
            dto=CreateEventInputDTO(
                user_id=USER,
                fields=EventFields(
                    title=title,
                    start_date=start_date,
                    has_year=True,
                    start_time=start_time,
                    end_date=None,
                    end_time=None,
                    location=None,
                    description=None,
                    repeat_yearly=repeat_yearly,
                    alert_leads_minutes=leads,
                ),
                origin="command",
                original_input=None,
            )
        )
        assert isinstance(event, EventDTO)
        return event

    def sweep(self, *, now: datetime) -> RollYearlyInteractor:
        return RollYearlyInteractor(
            event_repository=self.repository,
            user_clock=self.clock,
            alert_arming=fake_alert_arming(
                repository=self.repository, alerts=self.alerts
            ),
            now_provider=lambda: now,
        )

    def stored(self, *, event_id: uuid.UUID) -> StoredEventDTO:
        [row] = [row for row in self.repository.rows if row.id == event_id]
        return row

    def age(self, *, event_id: uuid.UUID, by: timedelta) -> None:
        """As if the event was last written ``by`` before NOW."""
        self.repository.rows = [
            replace(row, updated_at=NOW - by) if row.id == event_id else row
            for row in self.repository.rows
        ]

    def alert_times(self, *, event_id: uuid.UUID) -> list[datetime]:
        return [alert.fires_at for alert in self.alerts.alerts_by_event[event_id]]


async def test_an_ended_yearly_event_rolls_on_and_rearms_its_alerts() -> None:
    """C-11, FR-20, AD-4: after 12 Oct 2026 ends, 12 Oct 2027 and its alert."""
    world = World()
    event = await world.create(start_date=date(2026, 10, 12), leads=(1440, 10080))
    after_it_ended = datetime(2026, 10, 13, 1, tzinfo=KOLKATA).astimezone(UTC)

    counts = await world.sweep(now=after_it_ended).roll_yearly()

    stored = world.stored(event_id=event.id)
    assert counts.rolled == 1
    assert stored.starts_at == datetime(2027, 10, 12, tzinfo=KOLKATA)
    assert stored.alerts_pending is False
    assert world.alert_times(event_id=event.id) == [
        datetime(2027, 10, 5, 9, tzinfo=KOLKATA),
        datetime(2027, 10, 11, 9, tzinfo=KOLKATA),
    ]


async def test_a_leap_day_event_rolls_to_feb_28_and_back_to_feb_29() -> None:
    """C-11 with FR-10."""
    world = World()
    event = await world.create(title="Leap birthday", start_date=date(2028, 2, 29))
    after_2027 = datetime(2027, 3, 1, 1, tzinfo=KOLKATA).astimezone(UTC)
    world.repository.rows = [
        replace(
            row,
            starts_at=datetime(2027, 2, 28, tzinfo=KOLKATA),
            ends_at=datetime(2027, 3, 1, tzinfo=KOLKATA),
        )
        for row in world.repository.rows
    ]

    await world.sweep(now=after_2027).roll_yearly()

    assert world.stored(event_id=event.id).starts_at == datetime(
        2028, 2, 29, tzinfo=KOLKATA
    )


async def test_the_sweep_arms_an_event_left_pending() -> None:
    """C-12, 4.2 Q1: alerts failed at create; the next sweep sets them."""
    world = World()
    world.alerts.fail = True
    event = await world.create(
        title="Dentist",
        start_date=date(2026, 10, 9),
        start_time=time(16),
        repeat_yearly=False,
        leads=(60,),
    )
    world.alerts.fail = False
    assert world.stored(event_id=event.id).alerts_pending is True
    world.age(event_id=event.id, by=timedelta(minutes=5))

    counts = await world.sweep(now=NOW).roll_yearly()

    assert counts.repaired == 1
    assert world.stored(event_id=event.id).alerts_pending is False
    assert world.alert_times(event_id=event.id) == [
        datetime(2026, 10, 9, 15, tzinfo=KOLKATA)
    ]


async def test_the_sweep_leaves_an_event_a_request_is_still_arming() -> None:
    """D-20: the grace keeps the sweep from racing a request."""
    world = World()
    world.alerts.fail = True
    event = await world.create(start_date=date(2026, 10, 12))
    world.alerts.fail = False
    world.age(event_id=event.id, by=timedelta(seconds=30))

    counts = await world.sweep(now=NOW).roll_yearly()

    assert counts.repaired == 0
    assert world.stored(event_id=event.id).alerts_pending is True


async def test_the_nightly_count_names_only_long_pending_events() -> None:
    """C-13, NFR-4: one stuck for two hours, one pending for a minute."""
    world = World()
    world.alerts.fail = True
    stuck = await world.create(start_date=date(2026, 10, 12))
    fresh = await world.create(start_date=date(2026, 10, 13))
    world.age(event_id=stuck.id, by=timedelta(hours=2))
    world.age(event_id=fresh.id, by=timedelta(minutes=1))

    count = await ReconcileAlertsInteractor(
        event_repository=world.repository, now_provider=lambda: NOW
    ).reconcile_alerts()

    assert count == 1


async def test_a_timezone_change_across_the_date_line() -> None:
    """C-14, FR-12, FR-13, NFR-3: Kolkata to Pago Pago, UTC-11."""
    world = World()
    all_day = await world.create(start_date=date(2026, 10, 12), repeat_yearly=False)
    yearly_timed = await world.create(
        title="Anniversary dinner", start_date=date(2026, 10, 20), start_time=time(20)
    )
    one_time = await world.create(
        title="Flight",
        start_date=date(2026, 10, 9),
        start_time=time(6),
        repeat_yearly=False,
        leads=(180,),
    )
    world.clock = FakeEventUserClockPort(timezone="Pacific/Pago_Pago")
    pago_pago = ZoneInfo("Pacific/Pago_Pago")

    moved = await RezoneEventsInteractor(
        event_repository=world.repository,
        user_clock=world.clock,
        alert_arming=fake_alert_arming(
            repository=world.repository, alerts=world.alerts
        ),
        now_provider=lambda: NOW,
    ).rezone_events(user_id=USER)

    assert moved == 3
    assert world.stored(event_id=all_day.id).schedule.start_date == date(2026, 10, 12)
    assert world.stored(event_id=all_day.id).starts_at == datetime(
        2026, 10, 12, tzinfo=pago_pago
    )
    assert world.alert_times(event_id=all_day.id) == [
        datetime(2026, 10, 11, 9, tzinfo=pago_pago)
    ]
    assert world.stored(event_id=yearly_timed.id).starts_at == datetime(
        2026, 10, 20, 20, tzinfo=pago_pago
    )
    one_time_stored = world.stored(event_id=one_time.id)
    assert one_time_stored.starts_at == one_time.starts_at
    assert one_time_stored.schedule.start_date == date(2026, 10, 8)
    assert one_time_stored.schedule.start_time == time(13, 30)
    assert world.alert_times(event_id=one_time.id) == [
        one_time.starts_at - timedelta(hours=3)
    ]
    assert {
        world.stored(event_id=event.id).alerts_pending
        for event in (all_day, yearly_timed, one_time)
    } == {False}


async def test_a_second_run_moves_nothing() -> None:
    """Safe to repeat: an event already in the zone is skipped."""
    world = World()
    await world.create(start_date=date(2026, 10, 12))
    rezone = RezoneEventsInteractor(
        event_repository=world.repository,
        user_clock=world.clock,
        alert_arming=fake_alert_arming(
            repository=world.repository, alerts=world.alerts
        ),
        now_provider=lambda: NOW,
    )

    assert await rezone.rezone_events(user_id=USER) == 0
