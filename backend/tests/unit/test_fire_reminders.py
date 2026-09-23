"""Firing, Done and Snooze: TC-2.3 to TC-2.7, TC-2.9, and the sweep's half of
TC-2.11. In-memory fakes and a clock the test moves."""

import uuid
from dataclasses import replace
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.domains.reminders.graphql.errors import ReminderNotFoundError
from app.domains.reminders.interactors.create_reminder import CreateReminderInteractor
from app.domains.reminders.interactors.dtos import (
    MarkReminderDoneInputDTO,
    SnoozeReminderInputDTO,
)
from app.domains.reminders.interactors.fire_due import FireDueInteractor
from app.domains.reminders.interactors.fire_one import FireOneInteractor
from app.domains.reminders.interactors.mark_reminder_done import (
    MarkReminderDoneInteractor,
)
from app.domains.reminders.interactors.snooze_reminder import SnoozeReminderInteractor
from app.domains.reminders.interfaces.dtos import ReminderDTO, ReminderFields
from app.domains.reminders.services.firing import SnoozeOption
from app.domains.reminders.services.schedule import RepeatKind
from tests.fakes.fake_notification_port import FakeFiringQueue, FakeNotificationPort
from tests.fakes.fake_reminder_repository import FakeReminderRepository
from tests.fakes.fake_user_clock_port import FakeUserClockPort

KOLKATA = ZoneInfo("Asia/Kolkata")
# Wednesday 23 September 2026, 10:00 in Kolkata.
CREATED_AT = datetime(2026, 9, 23, 10, 0, tzinfo=KOLKATA).astimezone(UTC)
# Thursday 24 September, 19:00 in Kolkata.
TOMORROW_7PM = datetime(2026, 9, 24, 13, 30, tzinfo=UTC)


class Clock:
    def __init__(self) -> None:
        self.current = CREATED_AT

    def now(self) -> datetime:
        return self.current


class World:
    """One user's reminders, the notification list, and a clock."""

    def __init__(self) -> None:
        self.clock = Clock()
        self.repository = FakeReminderRepository(now_provider=self.clock.now)
        self.notifications = FakeNotificationPort()
        self.queue = FakeFiringQueue()
        self.user_id = uuid.uuid4()

    async def create(self, *, kind: RepeatKind = RepeatKind.NONE) -> ReminderDTO:
        outcome = await CreateReminderInteractor(
            reminder_repository=self.repository,
            user_clock=FakeUserClockPort(),
            now_provider=self.clock.now,
        ).create_reminder(
            user_id=self.user_id,
            fields=ReminderFields(
                description="Call Mom",
                local_date=date(2026, 9, 24),
                local_time=time(19),
                repeat_kind=kind,
                repeat_interval=1,
                repeat_weekdays=(),
                month_day=None,
            ),
            origin="command",
            original_input=None,
        )
        assert isinstance(outcome, ReminderDTO)
        return outcome

    def fire_one(self) -> FireOneInteractor:
        return FireOneInteractor(
            reminder_repository=self.repository,
            notifications=self.notifications,
            now_provider=self.clock.now,
        )

    def fire_due(self) -> FireDueInteractor:
        return FireDueInteractor(
            reminder_repository=self.repository,
            firing_queue=self.queue,
            now_provider=self.clock.now,
        )

    def done(self) -> MarkReminderDoneInteractor:
        return MarkReminderDoneInteractor(
            reminder_repository=self.repository,
            notifications=self.notifications,
            now_provider=self.clock.now,
        )

    def snooze(self) -> SnoozeReminderInteractor:
        return SnoozeReminderInteractor(
            reminder_repository=self.repository,
            notifications=self.notifications,
            user_clock=FakeUserClockPort(),
            now_provider=self.clock.now,
        )

    def row(self, *, reminder_id: uuid.UUID) -> ReminderDTO:
        return self.repository.rows[reminder_id]


async def test_a_one_time_reminder_fires_and_waits_for_the_user() -> None:
    """TC-2.3, FR-12, FR-23."""
    world = World()
    reminder = await world.create()
    world.clock.current = TOMORROW_7PM + timedelta(seconds=20)

    outcome = await world.fire_one().fire_one(
        reminder_id=reminder.id, scheduled_for=TOMORROW_7PM
    )

    fired = world.row(reminder_id=reminder.id)
    assert outcome == "fired"
    assert fired.state == "fired"
    assert fired.next_fire_at is None
    assert fired.summary.when_text == "Fired today, 7:00 PM"
    [announcement] = world.notifications.announcements.values()
    assert announcement.lateness == "on_time"
    assert announcement.detail == ""


async def test_a_recurring_reminder_moves_on_at_firing() -> None:
    """TC-2.4, FR-24: the next occurrence is set before any action."""
    world = World()
    reminder = await world.create(kind=RepeatKind.DAILY)
    world.clock.current = TOMORROW_7PM

    await world.fire_one().fire_one(reminder_id=reminder.id, scheduled_for=TOMORROW_7PM)

    fired = world.row(reminder_id=reminder.id)
    assert fired.state == "fired"
    assert fired.next_fire_at == TOMORROW_7PM + timedelta(days=1)
    [announcement] = world.notifications.announcements.values()
    assert announcement.detail == "Every day"


async def test_running_the_same_firing_twice_announces_once() -> None:
    """TC-2.5, FR-16, NFR-3."""
    world = World()
    reminder = await world.create()
    world.clock.current = TOMORROW_7PM

    first = await world.fire_one().fire_one(
        reminder_id=reminder.id, scheduled_for=TOMORROW_7PM
    )
    second = await world.fire_one().fire_one(
        reminder_id=reminder.id, scheduled_for=TOMORROW_7PM
    )

    assert (first, second) == ("fired", "skipped")
    assert len(world.repository.firings) == 1
    assert len(world.notifications.announcements) == 1


async def test_a_retry_after_a_failed_announcement_announces_it() -> None:
    """AD-3: the firing was written, the notification was not; the retry finds
    the firing and announces it, once."""
    world = World()
    reminder = await world.create()
    world.clock.current = TOMORROW_7PM
    world.notifications.fail_next_announce = True

    with pytest.raises(ConnectionError):
        await world.fire_one().fire_one(
            reminder_id=reminder.id, scheduled_for=TOMORROW_7PM
        )
    await world.fire_one().fire_one(reminder_id=reminder.id, scheduled_for=TOMORROW_7PM)

    assert len(world.repository.firings) == 1
    assert len(world.notifications.announcements) == 1


async def test_deleted_or_edited_reminders_do_not_fire() -> None:
    """TC-2.6, FR-30, X-3."""
    world = World()
    deleted = await world.create()
    edited = await world.create()
    await world.repository.soft_delete(user_id=world.user_id, reminder_id=deleted.id)
    # Edited after its job was queued: now due two hours later.
    world.repository.rows[edited.id] = replace(
        world.row(reminder_id=edited.id), next_fire_at=TOMORROW_7PM + timedelta(hours=2)
    )
    world.clock.current = TOMORROW_7PM

    outcomes = [
        await world.fire_one().fire_one(reminder_id=item.id, scheduled_for=TOMORROW_7PM)
        for item in (deleted, edited)
    ]

    assert outcomes == ["skipped", "skipped"]
    assert world.repository.firings == {}
    assert world.notifications.announcements == {}


async def test_a_reminder_two_days_late_is_marked_missed() -> None:
    """FR-18, AD-11."""
    world = World()
    reminder = await world.create()
    world.clock.current = TOMORROW_7PM + timedelta(days=2)

    await world.fire_one().fire_one(reminder_id=reminder.id, scheduled_for=TOMORROW_7PM)

    assert world.row(reminder_id=reminder.id).last_action == "missed"
    [announcement] = world.notifications.announcements.values()
    assert announcement.lateness == "missed"


async def test_done_closes_a_one_time_reminder() -> None:
    """TC-2.7, FR-19."""
    world = World()
    reminder = await world.create()
    world.clock.current = TOMORROW_7PM
    await world.fire_one().fire_one(reminder_id=reminder.id, scheduled_for=TOMORROW_7PM)

    closed = await world.done().mark_reminder_done(
        dto=MarkReminderDoneInputDTO(user_id=world.user_id, reminder_id=reminder.id)
    )

    assert (closed.state, closed.next_fire_at, closed.last_action) == (
        "done",
        None,
        "done",
    )
    assert [action for _, action in world.notifications.actions] == ["done"]


async def test_done_on_a_recurring_reminder_closes_only_that_occurrence() -> None:
    """TC-2.7, FR-20."""
    world = World()
    reminder = await world.create(kind=RepeatKind.DAILY)
    world.clock.current = TOMORROW_7PM
    await world.fire_one().fire_one(reminder_id=reminder.id, scheduled_for=TOMORROW_7PM)

    closed = await world.done().mark_reminder_done(
        dto=MarkReminderDoneInputDTO(user_id=world.user_id, reminder_id=reminder.id)
    )

    assert closed.state == "upcoming"
    assert closed.next_fire_at == TOMORROW_7PM + timedelta(days=1)


async def test_a_snoozed_series_fires_at_the_snooze_and_at_its_own_time() -> None:
    """TC-2.9, FR-21, FR-24, 4.2 decision 1."""
    world = World()
    reminder = await world.create(kind=RepeatKind.DAILY)
    world.clock.current = TOMORROW_7PM
    await world.fire_one().fire_one(reminder_id=reminder.id, scheduled_for=TOMORROW_7PM)

    snoozed = await world.snooze().snooze_reminder(
        dto=SnoozeReminderInputDTO(
            user_id=world.user_id, reminder_id=reminder.id, option=SnoozeOption.ONE_HOUR
        )
    )
    snooze_at = TOMORROW_7PM + timedelta(hours=1)
    assert snoozed.snoozed_until == snooze_at
    assert snoozed.next_due_at == snooze_at

    world.clock.current = snooze_at
    await world.fire_one().fire_one(reminder_id=reminder.id, scheduled_for=snooze_at)
    after_snooze = world.row(reminder_id=reminder.id)
    assert after_snooze.snoozed_until is None
    assert after_snooze.next_fire_at == TOMORROW_7PM + timedelta(days=1)

    world.clock.current = TOMORROW_7PM + timedelta(days=1)
    outcome = await world.fire_one().fire_one(
        reminder_id=reminder.id, scheduled_for=TOMORROW_7PM + timedelta(days=1)
    )
    assert outcome == "fired"
    assert len(world.repository.firings) == 3


async def test_done_and_snooze_on_another_users_reminder_are_not_found() -> None:
    world = World()
    reminder = await world.create()
    stranger = uuid.uuid4()

    with pytest.raises(ReminderNotFoundError):
        await world.done().mark_reminder_done(
            dto=MarkReminderDoneInputDTO(user_id=stranger, reminder_id=reminder.id)
        )
    with pytest.raises(ReminderNotFoundError):
        await world.snooze().snooze_reminder(
            dto=SnoozeReminderInputDTO(
                user_id=stranger, reminder_id=reminder.id, option=SnoozeOption.TOMORROW
            )
        )


async def test_two_sweeps_queue_each_due_occurrence_once() -> None:
    """TC-2.11's interactor half: the queue refuses a second copy."""
    world = World()
    due = await world.create()
    await world.create(kind=RepeatKind.DAILY)
    world.clock.current = TOMORROW_7PM - timedelta(minutes=1)
    not_yet = await world.fire_due().fire_due()
    world.clock.current = TOMORROW_7PM

    first = await world.fire_due().fire_due()
    second = await world.fire_due().fire_due()

    assert (not_yet, first, second) == (0, 2, 0)
    assert (due.id, TOMORROW_7PM) in world.queue.queued
