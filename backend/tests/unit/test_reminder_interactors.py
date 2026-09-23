"""Reminder use cases: TC-1.11, TC-1.13, TC-1.17, TC-1.18 and the grouping
TC-1.19 relies on. In-memory fakes, a fixed clock."""

import uuid
from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

import pytest

from app.domains.reminders.constants import MAX_ACTIVE_REMINDERS
from app.domains.reminders.graphql.errors import (
    InvalidReminderError,
    ReminderDeletedError,
    ReminderNotFoundError,
    ReminderTimePassedError,
)
from app.domains.reminders.interactors.create_reminder import CreateReminderInteractor
from app.domains.reminders.interactors.delete_reminder import DeleteReminderInteractor
from app.domains.reminders.interactors.dtos import (
    DeleteReminderInputDTO,
    ListRemindersInputDTO,
    UpdateReminderInputDTO,
)
from app.domains.reminders.interactors.list_reminders import ListRemindersInteractor
from app.domains.reminders.interactors.update_reminder import UpdateReminderInteractor
from app.domains.reminders.interfaces.dtos import (
    ReminderDTO,
    ReminderFields,
    ReminderLimitReached,
    ReminderNeedsWhen,
)
from app.domains.reminders.services.schedule import RepeatKind
from tests.fakes.fake_reminder_repository import FakeReminderRepository
from tests.fakes.fake_user_clock_port import FakeUserClockPort

KOLKATA = ZoneInfo("Asia/Kolkata")
# Wednesday 23 September 2026, 10:00 in Kolkata.
NOW = datetime(2026, 9, 23, 10, 0, tzinfo=KOLKATA).astimezone(UTC)


def _now() -> datetime:
    return NOW


def _fields(
    *,
    description: str = "Call Mom",
    local_date: date | None = date(2026, 9, 24),
    local_time: time | None = time(19),
    kind: RepeatKind = RepeatKind.NONE,
    weekdays: tuple[int, ...] = (),
    month_day: int | None = None,
) -> ReminderFields:
    return ReminderFields(
        description=description,
        local_date=local_date,
        local_time=local_time,
        repeat_kind=kind,
        repeat_interval=1,
        repeat_weekdays=weekdays,
        month_day=month_day,
    )


def _create(
    repository: FakeReminderRepository,
) -> CreateReminderInteractor:
    return CreateReminderInteractor(
        reminder_repository=repository,
        user_clock=FakeUserClockPort(),
        now_provider=_now,
    )


async def _created(
    *, repository: FakeReminderRepository, user_id: uuid.UUID, fields: ReminderFields
) -> ReminderDTO:
    outcome = await _create(repository).create_reminder(
        user_id=user_id, fields=fields, origin="command", original_input="/remind x"
    )
    assert isinstance(outcome, ReminderDTO)
    return outcome


async def test_create_resolves_tomorrow_evening_in_the_users_zone() -> None:
    reminder = await _created(
        repository=FakeReminderRepository(now_provider=_now),
        user_id=uuid.uuid4(),
        fields=_fields(),
    )
    assert reminder.next_fire_at == datetime(2026, 9, 24, 13, 30, tzinfo=UTC)
    assert reminder.summary.when_text == "Tomorrow, 7:00 PM"
    assert reminder.summary.repeat_text == "Does not repeat"
    assert reminder.schedule_timezone == "Asia/Kolkata"
    assert reminder.when_note is None


async def test_create_with_a_date_and_no_time_takes_the_default_time() -> None:
    """TC-1.11, FR-3."""
    reminder = await _created(
        repository=FakeReminderRepository(now_provider=_now),
        user_id=uuid.uuid4(),
        fields=_fields(local_date=date(2026, 10, 15), local_time=None),
    )
    assert reminder.spec.local_time == time(9)
    assert reminder.summary.when_text == "Thu 15 Oct, 9:00 AM"
    assert reminder.when_note == "No time given, so your default reminder time"


async def test_create_at_a_time_passed_today_moves_to_tomorrow() -> None:
    """FR-4: 7 AM said at 10 AM."""
    reminder = await _created(
        repository=FakeReminderRepository(now_provider=_now),
        user_id=uuid.uuid4(),
        fields=_fields(local_date=date(2026, 9, 23), local_time=time(7)),
    )
    assert reminder.summary.when_text == "Tomorrow, 7:00 AM"
    assert reminder.when_note == "7:00 AM has already passed today"


async def test_create_with_no_date_asks_and_writes_nothing() -> None:
    """TC-1.14's half in reminders, FR-2."""
    repository = FakeReminderRepository(now_provider=_now)
    outcome = await _create(repository).create_reminder(
        user_id=uuid.uuid4(),
        fields=_fields(description="Call the plumber", local_date=None),
        origin="command",
        original_input="/remind call the plumber",
    )
    assert outcome == ReminderNeedsWhen(description="Call the plumber")
    assert repository.rows == {}


async def test_daily_with_no_date_starts_today() -> None:
    reminder = await _created(
        repository=FakeReminderRepository(now_provider=_now),
        user_id=uuid.uuid4(),
        fields=_fields(kind=RepeatKind.DAILY, local_date=None, local_time=time(20)),
    )
    assert reminder.summary.when_text == "Today, 8:00 PM"
    assert reminder.summary.repeat_text == "Every day"


async def test_monthly_on_the_31st_first_fires_on_30_september() -> None:
    reminder = await _created(
        repository=FakeReminderRepository(now_provider=_now),
        user_id=uuid.uuid4(),
        fields=_fields(kind=RepeatKind.MONTHLY, local_date=None, month_day=31),
    )
    assert reminder.spec.repeat_month_day == 31
    assert reminder.summary.when_text == "Wed 30 Sep, 7:00 PM"
    assert reminder.when_note == "September has 30 days, so the last day"


async def test_the_101st_active_reminder_is_refused() -> None:
    """TC-1.13, FR-38."""
    repository = FakeReminderRepository(now_provider=_now)
    user_id = uuid.uuid4()
    for _ in range(MAX_ACTIVE_REMINDERS):
        await _created(repository=repository, user_id=user_id, fields=_fields())

    outcome = await _create(repository).create_reminder(
        user_id=user_id, fields=_fields(), origin="command", original_input=None
    )

    assert outcome == ReminderLimitReached(limit=MAX_ACTIVE_REMINDERS)
    assert len(repository.rows) == MAX_ACTIVE_REMINDERS


async def test_a_deleted_reminder_frees_a_place_under_the_cap() -> None:
    """TC-1.13: a done or deleted one does not count."""
    repository = FakeReminderRepository(now_provider=_now)
    user_id = uuid.uuid4()
    created = [
        await _created(repository=repository, user_id=user_id, fields=_fields())
        for _ in range(MAX_ACTIVE_REMINDERS)
    ]
    await DeleteReminderInteractor(reminder_repository=repository).delete_reminder(
        dto=DeleteReminderInputDTO(user_id=user_id, reminder_id=created[0].id)
    )

    outcome = await _create(repository).create_reminder(
        user_id=user_id, fields=_fields(), origin="command", original_input=None
    )

    assert isinstance(outcome, ReminderDTO)


def _update_dto(
    *,
    user_id: uuid.UUID,
    reminder_id: uuid.UUID,
    kind: RepeatKind = RepeatKind.WEEKLY,
    weekdays: tuple[int, ...] = (0,),
    start: date = date(2026, 9, 28),
    at: time = time(9, 30),
    description: str = "Standup notes",
) -> UpdateReminderInputDTO:
    return UpdateReminderInputDTO(
        user_id=user_id,
        reminder_id=reminder_id,
        description=description,
        start_date=start,
        local_time=at,
        repeat_kind=kind,
        repeat_interval=1,
        repeat_weekdays=weekdays,
    )


def _update(repository: FakeReminderRepository) -> UpdateReminderInteractor:
    return UpdateReminderInteractor(
        reminder_repository=repository,
        user_clock=FakeUserClockPort(),
        now_provider=_now,
    )


async def test_edit_replaces_the_series_and_recomputes_the_next_time() -> None:
    """FR-28."""
    repository = FakeReminderRepository(now_provider=_now)
    user_id = uuid.uuid4()
    reminder = await _created(repository=repository, user_id=user_id, fields=_fields())

    updated = await _update(repository).update_reminder(
        dto=_update_dto(user_id=user_id, reminder_id=reminder.id)
    )

    assert updated.summary.repeat_text == "Every week on Mon"
    assert updated.next_fire_at == datetime(2026, 9, 28, 4, 0, tzinfo=UTC)


async def test_edit_to_weekly_with_no_day_raises_the_paired_error() -> None:
    """TC-1.17."""
    repository = FakeReminderRepository(now_provider=_now)
    user_id = uuid.uuid4()
    reminder = await _created(repository=repository, user_id=user_id, fields=_fields())

    with pytest.raises(InvalidReminderError) as raised:
        await _update(repository).update_reminder(
            dto=_update_dto(user_id=user_id, reminder_id=reminder.id, weekdays=())
        )
    assert raised.value.field == "repeatWeekdays"


async def test_edit_with_empty_text_names_the_description_field() -> None:
    repository = FakeReminderRepository(now_provider=_now)
    user_id = uuid.uuid4()
    reminder = await _created(repository=repository, user_id=user_id, fields=_fields())

    with pytest.raises(InvalidReminderError) as raised:
        await _update(repository).update_reminder(
            dto=_update_dto(user_id=user_id, reminder_id=reminder.id, description=" ")
        )
    assert raised.value.field == "description"


async def test_edit_of_a_one_time_reminder_into_the_past_is_refused() -> None:
    """The design's ReminderEditPast."""
    repository = FakeReminderRepository(now_provider=_now)
    user_id = uuid.uuid4()
    reminder = await _created(repository=repository, user_id=user_id, fields=_fields())

    with pytest.raises(ReminderTimePassedError):
        await _update(repository).update_reminder(
            dto=_update_dto(
                user_id=user_id,
                reminder_id=reminder.id,
                kind=RepeatKind.NONE,
                weekdays=(),
                start=date(2026, 9, 23),
                at=time(7),
            )
        )


async def test_edit_after_a_delete_elsewhere_says_it_was_deleted() -> None:
    """The design's ReminderEditGone."""
    repository = FakeReminderRepository(now_provider=_now)
    user_id = uuid.uuid4()
    reminder = await _created(repository=repository, user_id=user_id, fields=_fields())
    await repository.soft_delete(user_id=user_id, reminder_id=reminder.id)

    with pytest.raises(ReminderDeletedError):
        await _update(repository).update_reminder(
            dto=_update_dto(user_id=user_id, reminder_id=reminder.id)
        )


async def test_edit_of_another_users_reminder_is_not_found() -> None:
    """NFR-6: the same answer as a missing id."""
    repository = FakeReminderRepository(now_provider=_now)
    reminder = await _created(
        repository=repository, user_id=uuid.uuid4(), fields=_fields()
    )

    with pytest.raises(ReminderNotFoundError):
        await _update(repository).update_reminder(
            dto=_update_dto(user_id=uuid.uuid4(), reminder_id=reminder.id)
        )


async def test_an_unchanged_monthly_edit_keeps_the_31st() -> None:
    repository = FakeReminderRepository(now_provider=_now)
    user_id = uuid.uuid4()
    reminder = await _created(
        repository=repository,
        user_id=user_id,
        fields=_fields(kind=RepeatKind.MONTHLY, local_date=None, month_day=31),
    )

    updated = await _update(repository).update_reminder(
        dto=_update_dto(
            user_id=user_id,
            reminder_id=reminder.id,
            kind=RepeatKind.MONTHLY,
            weekdays=(),
            start=reminder.spec.anchor_local_date,
            description="Pay rent",
        )
    )

    assert updated.spec.repeat_month_day == 31


async def test_delete_clears_the_next_fire_time() -> None:
    """TC-1.18, FR-29, FR-30."""
    repository = FakeReminderRepository(now_provider=_now)
    user_id = uuid.uuid4()
    reminder = await _created(repository=repository, user_id=user_id, fields=_fields())

    await DeleteReminderInteractor(reminder_repository=repository).delete_reminder(
        dto=DeleteReminderInputDTO(user_id=user_id, reminder_id=reminder.id)
    )

    assert repository.rows[reminder.id].next_fire_at is None
    assert await repository.get_by_id(user_id=user_id, reminder_id=reminder.id) is None


async def test_deleting_a_missing_reminder_is_not_found() -> None:
    with pytest.raises(ReminderNotFoundError):
        await DeleteReminderInteractor(
            reminder_repository=FakeReminderRepository(now_provider=_now)
        ).delete_reminder(
            dto=DeleteReminderInputDTO(user_id=uuid.uuid4(), reminder_id=uuid.uuid4())
        )


async def test_list_puts_upcoming_soonest_first() -> None:
    """TC-1.19's ordering, FR-26."""
    repository = FakeReminderRepository(now_provider=_now)
    user_id = uuid.uuid4()
    later = await _created(
        repository=repository,
        user_id=user_id,
        fields=_fields(description="Later", local_date=date(2026, 10, 15)),
    )
    sooner = await _created(
        repository=repository,
        user_id=user_id,
        fields=_fields(description="Sooner", local_date=date(2026, 9, 24)),
    )

    groups = await ListRemindersInteractor(
        reminder_repository=repository
    ).list_reminders(dto=ListRemindersInputDTO(user_id=user_id, search=None))

    assert [item.id for item in groups.upcoming] == [sooner.id, later.id]
    assert groups.needs_attention == []
    assert groups.done == []
