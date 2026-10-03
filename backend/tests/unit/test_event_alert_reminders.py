"""Epic 007, sub-plan 4.2, T-2.3: reminders' half of event alerts.

C-5 (soonest first under the cap), C-6 (alert rows stay out of reminders'
own lists) and C-7 (an alert fires as an event alert), plus FR-19, FR-21 and
FR-23 as reminders sees them. In-memory fakes and a fixed clock.
"""

import uuid
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.domains.reminders.constants import MAX_ACTIVE_REMINDERS
from app.domains.reminders.interactors.clear_event_alerts import (
    ClearEventAlertsInteractor,
)
from app.domains.reminders.interactors.create_reminder import CreateReminderInteractor
from app.domains.reminders.interactors.dtos import (
    ClearEventAlertsInputDTO,
    SetEventAlertsInputDTO,
)
from app.domains.reminders.interactors.fire_one import FireOneInteractor
from app.domains.reminders.interactors.set_event_alerts import (
    SetEventAlertsInteractor,
)
from app.domains.reminders.interfaces.dtos import (
    AlertNotSet,
    EventAlertRequest,
    ReminderDTO,
    ReminderFields,
)
from app.domains.reminders.services.schedule import RepeatKind
from tests.fakes.fake_notification_port import FakeNotificationPort
from tests.fakes.fake_reminder_repository import FakeReminderRepository
from tests.fakes.fake_user_clock_port import FakeUserClockPort

KOLKATA = ZoneInfo("Asia/Kolkata")
# Friday 2 October 2026, 10:00 in Kolkata.
NOW = datetime(2026, 10, 2, 10, 0, tzinfo=KOLKATA).astimezone(UTC)
WEEK_BEFORE = datetime(2026, 10, 13, 6, 0, tzinfo=KOLKATA).astimezone(UTC)
DAY_BEFORE = datetime(2026, 10, 19, 6, 0, tzinfo=KOLKATA).astimezone(UTC)
HOURS_BEFORE = datetime(2026, 10, 20, 3, 0, tzinfo=KOLKATA).astimezone(UTC)


def _now() -> datetime:
    return NOW


class World:
    """One user, their reminders, the notification list and a fixed clock."""

    def __init__(self) -> None:
        self.repository = FakeReminderRepository(now_provider=_now)
        self.notifications = FakeNotificationPort()
        self.user_id = uuid.uuid4()
        self.event_id = uuid.uuid4()

    async def set_alerts(self, *alerts: EventAlertRequest) -> list[AlertNotSet]:
        return await SetEventAlertsInteractor(
            reminder_repository=self.repository, user_clock=FakeUserClockPort()
        ).set_event_alerts(
            dto=SetEventAlertsInputDTO(
                user_id=self.user_id,
                event_id=self.event_id,
                title="Flight to Delhi",
                alerts=alerts,
                origin="command",
                now=NOW,
            )
        )

    async def clear_alerts(self) -> None:
        await ClearEventAlertsInteractor(
            reminder_repository=self.repository, notifications=self.notifications
        ).clear_event_alerts(
            dto=ClearEventAlertsInputDTO(user_id=self.user_id, event_id=self.event_id)
        )

    async def add_reminders(self, *, count: int) -> None:
        create = CreateReminderInteractor(
            reminder_repository=self.repository,
            user_clock=FakeUserClockPort(),
            now_provider=_now,
        )
        for _ in range(count):
            outcome = await create.create_reminder(
                user_id=self.user_id,
                fields=ReminderFields(
                    description="Water the plants",
                    local_date=date(2026, 10, 3),
                    local_time=time(9),
                    repeat_kind=RepeatKind.NONE,
                    repeat_interval=1,
                    repeat_weekdays=(),
                    month_day=None,
                ),
                origin="command",
                original_input=None,
            )
            assert isinstance(outcome, ReminderDTO)

    def alert_times(self) -> list[datetime | None]:
        return [
            row.next_fire_at
            for row in self.repository.live_alerts_for(event_id=self.event_id)
        ]


def _alert(*, fires_at: datetime, lead: str = "1 day before") -> EventAlertRequest:
    return EventAlertRequest(fires_at=fires_at, detail=f"{lead} · Tue 20 Oct, 6:00 AM")


async def test_every_alert_is_a_one_time_row_carrying_its_event() -> None:
    """FR-14 for reminders: one row per alert, with its event's id."""
    world = World()

    not_set = await world.set_alerts(
        _alert(fires_at=DAY_BEFORE), _alert(fires_at=WEEK_BEFORE, lead="1 week before")
    )

    assert not_set == []
    rows = world.repository.live_alerts_for(event_id=world.event_id)
    assert [row.next_fire_at for row in rows] == [WEEK_BEFORE, DAY_BEFORE]
    assert {row.spec.repeat_kind for row in rows} == {RepeatKind.NONE}
    assert rows[0].description == "Flight to Delhi"
    assert rows[0].alert_detail == "1 week before · Tue 20 Oct, 6:00 AM"
    assert rows[0].spec.anchor_local_date == date(2026, 10, 13)
    assert rows[0].spec.local_time == time(6)


async def test_a_passed_alert_is_not_set_and_the_rest_are() -> None:
    """FR-19: only the passed alert is named."""
    world = World()
    passed = NOW - timedelta(days=1)

    not_set = await world.set_alerts(
        _alert(fires_at=passed), _alert(fires_at=DAY_BEFORE)
    )

    assert not_set == [AlertNotSet(fires_at=passed, reason="passed")]
    assert world.alert_times() == [DAY_BEFORE]


async def test_at_the_cap_the_soonest_firing_alerts_are_set() -> None:
    """C-5, FR-33 and AD-8: at 98 active reminders, two of three fit."""
    world = World()
    await world.add_reminders(count=MAX_ACTIVE_REMINDERS - 2)

    not_set = await world.set_alerts(
        _alert(fires_at=HOURS_BEFORE),
        _alert(fires_at=DAY_BEFORE),
        _alert(fires_at=WEEK_BEFORE),
    )

    assert not_set == [AlertNotSet(fires_at=HOURS_BEFORE, reason="cap")]
    assert world.alert_times() == [WEEK_BEFORE, DAY_BEFORE]


async def test_the_events_own_alerts_do_not_count_against_their_replacement() -> None:
    """FR-33: re-setting a full event's alerts must not refuse them."""
    world = World()
    await world.add_reminders(count=MAX_ACTIVE_REMINDERS - 2)
    await world.set_alerts(_alert(fires_at=WEEK_BEFORE), _alert(fires_at=DAY_BEFORE))

    not_set = await world.set_alerts(
        _alert(fires_at=WEEK_BEFORE), _alert(fires_at=DAY_BEFORE)
    )

    assert not_set == []
    assert world.alert_times() == [WEEK_BEFORE, DAY_BEFORE]


async def test_setting_again_replaces_the_set() -> None:
    """FR-21 and FR-22: moved and removed alerts leave no old row behind."""
    world = World()
    await world.set_alerts(_alert(fires_at=WEEK_BEFORE), _alert(fires_at=DAY_BEFORE))

    await world.set_alerts(_alert(fires_at=HOURS_BEFORE))

    assert world.alert_times() == [HOURS_BEFORE]


async def test_an_empty_set_clears_without_hiding_notifications() -> None:
    world = World()
    await world.set_alerts(_alert(fires_at=DAY_BEFORE))

    await world.set_alerts()

    assert world.alert_times() == []
    assert world.notifications.hidden_event_ids == []


async def test_clearing_removes_every_alert_and_hides_their_notifications() -> None:
    """FR-23: a deleted event's alerts never fire, and their notifications go."""
    world = World()
    await world.set_alerts(_alert(fires_at=WEEK_BEFORE), _alert(fires_at=DAY_BEFORE))

    await world.clear_alerts()

    assert world.alert_times() == []
    assert world.notifications.hidden_event_ids == [world.event_id]


async def test_alert_rows_stay_out_of_reminders_own_lists() -> None:
    """C-6, FR-32: the list every reminders screen and job reads skips them."""
    world = World()
    await world.add_reminders(count=1)
    await world.set_alerts(_alert(fires_at=DAY_BEFORE))

    listed = await world.repository.list_for_user(user_id=world.user_id)

    assert [row.description for row in listed] == ["Water the plants"]
    assert await world.repository.count_active_for_user(user_id=world.user_id) == 2


async def test_an_alert_fires_as_an_event_alert_with_its_line() -> None:
    """C-7, FR-17 and FR-18: the announcement names the event and its row."""
    world = World()
    await world.set_alerts(_alert(fires_at=DAY_BEFORE))
    alert_row = world.repository.live_alerts_for(event_id=world.event_id)[0]

    outcome = await FireOneInteractor(
        reminder_repository=world.repository,
        notifications=world.notifications,
        now_provider=lambda: DAY_BEFORE,
    ).fire_one(reminder_id=alert_row.id, scheduled_for=DAY_BEFORE)

    assert outcome == "fired"
    announcement = next(iter(world.notifications.announcements.values()))
    assert announcement.event_id == world.event_id
    assert announcement.reminder_id == alert_row.id
    assert announcement.title == "Flight to Delhi"
    assert announcement.detail == "1 day before · Tue 20 Oct, 6:00 AM"
