"""Sub-plan 4.4: timezone moves (TC-4.1 to TC-4.3), reconciliation (TC-4.5),
the firing kill switch (TC-4.6) and the 90-day purge. In-memory fakes and a
clock the test moves."""

import uuid
from dataclasses import replace
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from structlog.testing import capture_logs

from app.domains.notifications.interactors.purge_old_notifications import (
    PurgeOldNotificationsInteractor,
)
from app.domains.notifications.interfaces.dtos import NotificationDTO
from app.domains.reminders.interactors.create_reminder import CreateReminderInteractor
from app.domains.reminders.interactors.fire_due import FireDueInteractor
from app.domains.reminders.interactors.reconcile_reminders import (
    ReconcileRemindersInteractor,
)
from app.domains.reminders.interactors.rezone_reminders import (
    RezoneRemindersInteractor,
)
from app.domains.reminders.interfaces.dtos import ReminderDTO, ReminderFields
from app.domains.reminders.services.schedule import RepeatKind
from tests.fakes.fake_notification_port import FakeFiringQueue
from tests.fakes.fake_notification_repository import FakeNotificationRepository
from tests.fakes.fake_reminder_repository import FakeReminderRepository
from tests.fakes.fake_user_clock_port import FakeUserClockPort

KOLKATA = ZoneInfo("Asia/Kolkata")
# Wednesday 23 September 2026, 10:00 in Kolkata.
CREATED_AT = datetime(2026, 9, 23, 10, 0, tzinfo=KOLKATA).astimezone(UTC)
# Thursday 24 September, 19:00 in Kolkata.
TOMORROW_7PM_KOLKATA = datetime(2026, 9, 24, 13, 30, tzinfo=UTC)


class Clock:
    def __init__(self) -> None:
        self.current = CREATED_AT

    def now(self) -> datetime:
        return self.current


class World:
    """One user's reminders in Kolkata, and a clock."""

    def __init__(self) -> None:
        self.clock = Clock()
        self.repository = FakeReminderRepository(now_provider=self.clock.now)
        self.user_id = uuid.uuid4()

    async def create(self, *, kind: RepeatKind = RepeatKind.NONE) -> ReminderDTO:
        outcome = await CreateReminderInteractor(
            reminder_repository=self.repository,
            user_clock=FakeUserClockPort(timezone="Asia/Kolkata"),
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

    async def move_to(self, *, timezone: str) -> int:
        return await RezoneRemindersInteractor(
            reminder_repository=self.repository,
            user_clock=FakeUserClockPort(timezone=timezone),
            now_provider=self.clock.now,
        ).rezone_reminders(user_id=self.user_id)

    def row(self, *, reminder_id: uuid.UUID) -> ReminderDTO:
        return self.repository.rows[reminder_id]


async def test_a_daily_reminder_keeps_its_clock_time_in_the_new_zone() -> None:
    """TC-4.1, FR-10, X-6: 7 PM Kolkata becomes 7 PM London."""
    world = World()
    reminder = await world.create(kind=RepeatKind.DAILY)

    moved_count = await world.move_to(timezone="Europe/London")

    moved = world.row(reminder_id=reminder.id)
    assert moved_count == 1
    assert moved.schedule_timezone == "Europe/London"
    assert moved.spec.local_time == time(19)
    # 19:00 British Summer Time on Thursday 24 September.
    assert moved.next_fire_at == datetime(2026, 9, 24, 18, 0, tzinfo=UTC)


async def test_the_clock_time_holds_across_a_daylight_saving_change() -> None:
    """TC-4.1, FR-9: moved to New York, it stays 7 PM on both sides of 1 November."""
    world = World()
    reminder = await world.create(kind=RepeatKind.DAILY)
    world.clock.current = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)

    await world.move_to(timezone="America/New_York")

    moved = world.row(reminder_id=reminder.id)
    # 19:00 Eastern Standard Time, the evening daylight saving ends.
    assert moved.next_fire_at == datetime(2026, 11, 2, 0, 0, tzinfo=UTC)
    assert moved.spec.local_time == time(19)


async def test_a_one_time_reminder_keeps_its_moment() -> None:
    """TC-4.2, FR-11, X-6: the instant stays; its local words move."""
    world = World()
    reminder = await world.create()

    await world.move_to(timezone="Europe/London")

    moved = world.row(reminder_id=reminder.id)
    assert moved.next_fire_at == TOMORROW_7PM_KOLKATA
    assert moved.spec.one_time_at == TOMORROW_7PM_KOLKATA
    assert moved.schedule_timezone == "Europe/London"
    assert moved.spec.local_time == time(14, 30)
    assert moved.spec.anchor_local_date == date(2026, 9, 24)


async def test_a_snooze_stays_and_done_or_deleted_reminders_are_left_alone() -> None:
    """TC-4.3."""
    world = World()
    snoozed = await world.create(kind=RepeatKind.DAILY)
    done = await world.create(kind=RepeatKind.DAILY)
    deleted = await world.create(kind=RepeatKind.DAILY)
    snooze_at = datetime(2026, 9, 23, 5, 0, tzinfo=UTC)
    world.repository.rows[snoozed.id] = replace(
        world.row(reminder_id=snoozed.id), snoozed_until=snooze_at
    )
    world.repository.rows[done.id] = replace(
        world.row(reminder_id=done.id), state="done"
    )
    await world.repository.soft_delete(user_id=world.user_id, reminder_id=deleted.id)

    moved_count = await world.move_to(timezone="Europe/London")

    assert moved_count == 1
    assert world.row(reminder_id=snoozed.id).snoozed_until == snooze_at
    assert world.row(reminder_id=done.id).schedule_timezone == "Asia/Kolkata"
    assert world.row(reminder_id=deleted.id).schedule_timezone == "Asia/Kolkata"


async def test_a_firing_between_read_and_write_is_retried() -> None:
    """TC-4.3, 4.4 §9: the row changed under the move, so it is read again."""
    world = World()
    reminder = await world.create(kind=RepeatKind.DAILY)
    interrupted: list[uuid.UUID] = []

    def fire_first_time(reminder_id: uuid.UUID) -> None:
        if interrupted:
            return
        interrupted.append(reminder_id)
        world.repository.rows[reminder_id] = replace(
            world.row(reminder_id=reminder_id),
            updated_at=CREATED_AT + timedelta(seconds=1),
        )

    world.repository.before_rezone = fire_first_time

    moved_count = await world.move_to(timezone="Europe/London")

    assert interrupted == [reminder.id]
    assert moved_count == 1
    assert world.row(reminder_id=reminder.id).schedule_timezone == "Europe/London"


async def test_an_edit_made_during_the_move_wins() -> None:
    """TC-4.3, 4.4 §9: an edit already saved in the new zone is not redone."""
    world = World()
    reminder = await world.create(kind=RepeatKind.DAILY)

    def edit_in_new_zone(reminder_id: uuid.UUID) -> None:
        current = world.row(reminder_id=reminder_id)
        world.repository.rows[reminder_id] = replace(
            current,
            spec=replace(current.spec, local_time=time(8)),
            schedule_timezone="Europe/London",
            updated_at=CREATED_AT + timedelta(seconds=1),
        )

    world.repository.before_rezone = edit_in_new_zone

    moved_count = await world.move_to(timezone="Europe/London")

    edited = world.row(reminder_id=reminder.id)
    assert moved_count == 0
    assert edited.spec.local_time == time(8)


async def test_reconcile_logs_reminders_lost_past_five_minutes() -> None:
    """TC-4.5, NFR-4: 6 minutes overdue is lost; 4 minutes is not yet."""
    world = World()
    reminder = await world.create()
    reconcile = ReconcileRemindersInteractor(
        reminder_repository=world.repository, now_provider=world.clock.now
    )

    world.clock.current = TOMORROW_7PM_KOLKATA + timedelta(minutes=4)
    with capture_logs() as early_logs:
        early_count = await reconcile.reconcile()

    world.clock.current = TOMORROW_7PM_KOLKATA + timedelta(minutes=6)
    with capture_logs() as late_logs:
        late_count = await reconcile.reconcile()

    assert early_count == 0
    assert early_logs == []
    assert late_count == 1
    [lost] = late_logs
    assert lost["event"] == "reminders.lost"
    assert lost["log_level"] == "error"
    assert lost["reminder_id"] == str(reminder.id)
    assert lost["minutes_overdue"] == 6
    # T6: ids and times only.
    assert "Call Mom" not in str(lost)


async def test_reconcile_ignores_done_and_deleted_reminders() -> None:
    """TC-4.5."""
    world = World()
    done = await world.create()
    deleted = await world.create()
    world.repository.rows[done.id] = replace(
        world.row(reminder_id=done.id), state="done"
    )
    await world.repository.soft_delete(user_id=world.user_id, reminder_id=deleted.id)
    world.clock.current = TOMORROW_7PM_KOLKATA + timedelta(hours=1)

    lost_count = await ReconcileRemindersInteractor(
        reminder_repository=world.repository, now_provider=world.clock.now
    ).reconcile()

    assert lost_count == 0


async def test_with_firing_switched_off_the_sweep_queues_nothing() -> None:
    """TC-4.6, index §9."""
    world = World()
    await world.create()
    world.clock.current = TOMORROW_7PM_KOLKATA + timedelta(seconds=5)
    queue = FakeFiringQueue()

    queued_count = await FireDueInteractor(
        reminder_repository=world.repository,
        firing_queue=queue,
        now_provider=world.clock.now,
        is_firing_enabled=False,
    ).fire_due()

    assert queued_count == 0
    assert queue.queued == set()


def _notification(*, user_id: uuid.UUID, created_at: datetime) -> NotificationDTO:
    return NotificationDTO(
        id=uuid.uuid4(),
        user_id=user_id,
        kind="reminder",
        source_id=uuid.uuid4(),
        target_id=uuid.uuid4(),
        title="Call Mom",
        detail="",
        marker="on_time",
        occurred_at=created_at,
        time_zone="Asia/Kolkata",
        created_at=created_at,
        read_at=None,
        action=None,
        acted_at=None,
        show_popup=True,
    )


async def test_the_purge_takes_only_notifications_past_ninety_days() -> None:
    """FR-40, TC-4.8's rule in memory: 91 days goes, 89 days stays."""
    now = datetime(2026, 12, 31, 3, 15, tzinfo=UTC)
    user_id = uuid.uuid4()
    repository = FakeNotificationRepository()
    old = _notification(user_id=user_id, created_at=now - timedelta(days=91))
    recent = _notification(user_id=user_id, created_at=now - timedelta(days=89))
    repository.rows = {old.id: old, recent.id: recent}

    purged_count = await PurgeOldNotificationsInteractor(
        notification_repository=repository, now_provider=lambda: now
    ).purge_old_notifications()

    page = await repository.list_page(user_id=user_id, cursor=None, limit=30)
    assert purged_count == 1
    assert [item.id for item in page.items] == [recent.id]
    assert await repository.count_unread(user_id=user_id) == 1
    assert old.id in repository.rows
