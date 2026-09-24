"""Slice 4 against a real database, and the cross-slice cases it owes.

TC-4.7 (X-6): a timezone change over the API queues the move, and the move
keeps a daily 7 PM at 7 PM London and a one-time reminder at its instant.
TC-4.8: the 90-day purge. TC-4.9: one user's move leaves another's alone.
TC-4.10: X-1 and X-2. X-3 and X-4 are in ``test_fire_reminders.py`` and
``test_firing_and_notifications.py``; X-5 is covered by the isolation tests in
``test_reminders_graphql.py``, ``test_firing_and_notifications.py`` and
``test_notification_subscription.py``.
"""

import uuid
from collections.abc import Callable
from datetime import UTC, date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql import text

from app.core import auth as auth_module
from app.core.db import user_transaction
from app.core.deps import (
    build_purge_old_notifications_interactor,
    build_rezone_reminders_interactor,
)
from app.core.settings import Settings
from app.domains.identity.repositories.settings_repository import SqlSettingsRepository
from app.domains.identity.services.identity_service import IdentityService
from app.domains.notifications.adapters.identity_settings_adapter import (
    IdentityDeliverySettingsAdapter,
)
from app.domains.notifications.repositories.notification_repository import (
    SqlNotificationRepository,
)
from app.domains.notifications.services.notification_service import (
    NotificationService,
)
from app.domains.reminders.adapters.identity_clock_adapter import (
    IdentityUserClockAdapter,
)
from app.domains.reminders.adapters.notifications_adapter import NotificationsAdapter
from app.domains.reminders.interactors.create_reminder import CreateReminderInteractor
from app.domains.reminders.interactors.dtos import UpdateReminderInputDTO
from app.domains.reminders.interactors.fire_one import FireOneInteractor
from app.domains.reminders.interactors.update_reminder import UpdateReminderInteractor
from app.domains.reminders.interfaces.dtos import ReminderDTO, ReminderFields
from app.domains.reminders.repositories.reminder_repository import SqlReminderRepository
from app.domains.reminders.services.schedule import RepeatKind
from tests.fakes.fake_email import FakeEmailQueue

KOLKATA = ZoneInfo("Asia/Kolkata")
LONDON = ZoneInfo("Europe/London")


def _now() -> datetime:
    return datetime.now(UTC)


def _kolkata_tomorrow() -> date:
    return datetime.now(KOLKATA).date() + timedelta(days=1)


async def _set_timezone(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    user_id: uuid.UUID,
    timezone: str,
) -> None:
    async with session_factory() as session:
        await SqlSettingsRepository(session).upsert(user_id=user_id, timezone=timezone)


async def _create(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    user_id: uuid.UUID,
    kind: RepeatKind,
    weekdays: tuple[int, ...] = (),
) -> ReminderDTO:
    async with session_factory() as session:
        outcome = await CreateReminderInteractor(
            reminder_repository=SqlReminderRepository(session),
            user_clock=IdentityUserClockAdapter(
                identity_service=IdentityService(
                    settings_repository=SqlSettingsRepository(session)
                )
            ),
            now_provider=_now,
        ).create_reminder(
            user_id=user_id,
            fields=ReminderFields(
                description="Call Mom",
                local_date=_kolkata_tomorrow(),
                local_time=time(19),
                repeat_kind=kind,
                repeat_interval=1,
                repeat_weekdays=weekdays,
                month_day=None,
            ),
            origin="command",
            original_input="/remind Call Mom tomorrow at 7pm",
        )
    assert isinstance(outcome, ReminderDTO)
    return outcome


async def _read(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    user_id: uuid.UUID,
    reminder_id: uuid.UUID,
) -> ReminderDTO:
    async with session_factory() as session:
        reminder = await SqlReminderRepository(session).get_by_id(
            user_id=user_id, reminder_id=reminder_id
        )
    assert reminder is not None
    return reminder


def _fire_one(
    *, session: AsyncSession, now_provider: Callable[[], datetime]
) -> FireOneInteractor:
    """As deps wires it, on a clock the test sets; email off, as shipped."""
    service = NotificationService(
        notification_repository=SqlNotificationRepository(session),
        delivery_settings=IdentityDeliverySettingsAdapter(
            identity_service=IdentityService(
                settings_repository=SqlSettingsRepository(session)
            )
        ),
        email_queue=FakeEmailQueue(),
        is_email_configured=False,
        now_provider=now_provider,
    )
    return FireOneInteractor(
        reminder_repository=SqlReminderRepository(session),
        notifications=NotificationsAdapter(notification_service=service),
        now_provider=now_provider,
    )


async def _count(
    session_factory: async_sessionmaker[AsyncSession], *, sql: str, **params: Any
) -> int:
    async with session_factory() as session:
        count = await session.scalar(text(sql), params)
    return int(count or 0)


@pytest.fixture
def signing_key(monkeypatch: pytest.MonkeyPatch) -> ec.EllipticCurvePrivateKey:
    key = ec.generate_private_key(ec.SECP256R1())
    public_key = key.public_key()

    class FakeKey:
        key = public_key

    class FakeClient:
        def get_signing_key_from_jwt(self, _token: str) -> FakeKey:
            return FakeKey()

    monkeypatch.setattr(auth_module, "_get_jwks_client", lambda _s: FakeClient())
    return key


def _headers(
    key: ec.EllipticCurvePrivateKey, settings: Settings, *, user_id: uuid.UUID
) -> dict[str, str]:
    claims: dict[str, Any] = {
        "sub": str(user_id),
        "iss": settings.jwt_issuer,
        "exp": datetime.now(UTC) + timedelta(hours=1),
    }
    return {"Authorization": f"Bearer {jwt.encode(claims, key, algorithm='ES256')}"}


UPDATE_TIMEZONE = """
mutation($input: UpdateTimezoneInput!) {
  updateTimezone(input: $input) { __typename ... on Settings { timezone } }
}
"""


async def test_a_timezone_change_moves_reminders_as_the_prd_says(
    client: AsyncClient,
    signing_key: ec.EllipticCurvePrivateKey,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
    job_queue: None,
) -> None:
    """TC-4.7, TC-4.9, X-6, FR-10, FR-11, AD-6."""
    user_a, user_b = two_users
    for user_id in two_users:
        await _set_timezone(session_factory, user_id=user_id, timezone="Asia/Kolkata")
    daily = await _create(session_factory, user_id=user_a, kind=RepeatKind.DAILY)
    one_time = await _create(session_factory, user_id=user_a, kind=RepeatKind.NONE)
    other_users = await _create(session_factory, user_id=user_b, kind=RepeatKind.DAILY)

    response = await client.post(
        "/graphql",
        json={
            "query": UPDATE_TIMEZONE,
            "variables": {"input": {"timezone": "Europe/London"}},
        },
        headers=_headers(signing_key, settings, user_id=user_a),
    )
    queued = await _count(
        session_factory,
        sql="SELECT count(*) FROM procrastinate.procrastinate_jobs "
        "WHERE task_name = 'reminders.timezone_changed' AND queueing_lock = :lock",
        lock=f"tz:{user_a}",
    )
    # What the queued job runs.
    async with session_factory() as session:
        moved_count = await build_rezone_reminders_interactor(session).rezone_reminders(
            user_id=user_a
        )

    moved_daily = await _read(session_factory, user_id=user_a, reminder_id=daily.id)
    moved_one_time = await _read(
        session_factory, user_id=user_a, reminder_id=one_time.id
    )
    untouched = await _read(session_factory, user_id=user_b, reminder_id=other_users.id)
    assert response.json()["data"]["updateTimezone"]["timezone"] == "Europe/London"
    assert queued == 1
    assert moved_count == 2
    assert moved_daily.next_fire_at is not None
    assert moved_daily.next_fire_at.astimezone(LONDON).time() == time(19)
    assert moved_one_time.next_fire_at == one_time.next_fire_at
    assert moved_one_time.schedule_timezone == "Europe/London"
    assert untouched.schedule_timezone == "Asia/Kolkata"
    assert untouched.next_fire_at == other_users.next_fire_at


async def test_a_firing_queued_for_the_old_zone_fires_nothing(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """TC-4.7: 4.2's due-time check stops the stale job; the sweep queues anew."""
    user_a, _ = two_users
    await _set_timezone(session_factory, user_id=user_a, timezone="Asia/Kolkata")
    daily = await _create(session_factory, user_id=user_a, kind=RepeatKind.DAILY)
    old_due = daily.next_fire_at
    assert old_due is not None
    await _set_timezone(session_factory, user_id=user_a, timezone="Europe/London")
    async with session_factory() as session:
        await build_rezone_reminders_interactor(session).rezone_reminders(
            user_id=user_a
        )

    async with session_factory() as session:
        outcome = await _fire_one(
            session=session, now_provider=lambda: old_due + timedelta(seconds=10)
        ).fire_one(reminder_id=daily.id, scheduled_for=old_due)

    firings = await _count(
        session_factory,
        sql="SELECT count(*) FROM reminder_firings WHERE reminder_id = :id",
        id=daily.id,
    )
    assert outcome == "skipped"
    assert firings == 0


async def test_a_reminder_fires_once_at_its_local_time(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """X-1, FR-9, FR-12, FR-14, FR-16. Capture's reading of the sentence is
    slice 1's `test_remind_capture.py`; this starts from the fields it yields."""
    user_a, _ = two_users
    await _set_timezone(session_factory, user_id=user_a, timezone="Asia/Kolkata")
    reminder = await _create(session_factory, user_id=user_a, kind=RepeatKind.NONE)
    due = reminder.next_fire_at
    assert due is not None
    assert due.astimezone(KOLKATA) == datetime.combine(
        _kolkata_tomorrow(), time(19), tzinfo=KOLKATA
    )

    for _ in range(2):
        async with session_factory() as session:
            await _fire_one(
                session=session, now_provider=lambda: due + timedelta(seconds=10)
            ).fire_one(reminder_id=reminder.id, scheduled_for=due)

    params = {"id": reminder.id}
    firings = await _count(
        session_factory,
        sql="SELECT count(*) FROM reminder_firings WHERE reminder_id = :id",
        **params,
    )
    notifications = await _count(
        session_factory,
        sql="SELECT count(*) FROM notifications WHERE target_id = :id",
        **params,
    )
    emails = await _count(
        session_factory,
        sql="SELECT count(*) FROM notification_deliveries d "
        "JOIN notifications n ON n.id = d.notification_id "
        "WHERE n.target_id = :id AND d.channel = 'email'",
        **params,
    )
    assert (firings, notifications, emails) == (1, 1, 1)


async def test_a_weekly_reminder_moved_to_monday_never_fires_on_tuesday(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """X-2, FR-28, FR-30."""
    user_a, _ = two_users
    await _set_timezone(session_factory, user_id=user_a, timezone="Asia/Kolkata")
    tuesdays = await _create(
        session_factory, user_id=user_a, kind=RepeatKind.WEEKLY, weekdays=(1,)
    )
    tuesday_due = tuesdays.next_fire_at
    assert tuesday_due is not None
    assert tuesday_due.astimezone(KOLKATA).weekday() == 1

    async with session_factory() as session:
        edited = await UpdateReminderInteractor(
            reminder_repository=SqlReminderRepository(session),
            user_clock=IdentityUserClockAdapter(
                identity_service=IdentityService(
                    settings_repository=SqlSettingsRepository(session)
                )
            ),
            now_provider=_now,
        ).update_reminder(
            dto=UpdateReminderInputDTO(
                user_id=user_a,
                reminder_id=tuesdays.id,
                description="Call Mom",
                start_date=_kolkata_tomorrow(),
                local_time=time(19),
                repeat_kind=RepeatKind.WEEKLY,
                repeat_interval=1,
                repeat_weekdays=(0,),
            )
        )
        outcome = await _fire_one(
            session=session, now_provider=lambda: tuesday_due + timedelta(seconds=10)
        ).fire_one(reminder_id=tuesdays.id, scheduled_for=tuesday_due)

    assert edited.next_fire_at is not None
    assert edited.next_fire_at.astimezone(KOLKATA).weekday() == 0
    assert outcome == "skipped"


async def _seed_notification(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    user_id: uuid.UUID,
    age: timedelta,
) -> uuid.UUID:
    notification_id = uuid.uuid4()
    created_at = datetime.now(UTC) - age
    async with session_factory() as session, user_transaction(session, user_id) as s:
        await s.execute(
            text(
                "INSERT INTO notifications (id, user_id, kind, title, detail, "
                "marker, occurred_at, created_at) VALUES (:id, :user_id, "
                "'reminder', 'Call Mom', '', 'on_time', :at, :at)"
            ),
            {"id": notification_id, "user_id": user_id, "at": created_at},
        )
    return notification_id


async def test_the_purge_takes_notifications_past_ninety_days_off_the_list(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """TC-4.8, FR-40: stamped, not deleted; every panel read skips it."""
    user_a, _ = two_users
    await _set_timezone(session_factory, user_id=user_a, timezone="Asia/Kolkata")
    reminder = await _create(session_factory, user_id=user_a, kind=RepeatKind.DAILY)
    old_id = await _seed_notification(
        session_factory, user_id=user_a, age=timedelta(days=91)
    )
    recent_id = await _seed_notification(
        session_factory, user_id=user_a, age=timedelta(days=89)
    )

    async with session_factory() as session:
        purged_count = await build_purge_old_notifications_interactor(
            session
        ).purge_old_notifications()
    async with session_factory() as session:
        repository = SqlNotificationRepository(session)
        page = await repository.list_page(user_id=user_a, cursor=None, limit=30)
        unread = await repository.count_unread(user_id=user_a)
        marked = await repository.mark_all_read(user_id=user_a, now=_now())
        old_read = await repository.get(user_id=user_a, notification_id=old_id)

    old_row_kept = await _count(
        session_factory,
        sql="SELECT count(*) FROM notifications "
        "WHERE id = :id AND deleted_at IS NOT NULL AND read_at IS NULL",
        id=old_id,
    )
    assert purged_count >= 1
    assert [item.id for item in page.items] == [recent_id]
    assert (unread, marked) == (1, 1)
    assert old_read is None
    assert old_row_kept == 1
    await _read(session_factory, user_id=user_a, reminder_id=reminder.id)
