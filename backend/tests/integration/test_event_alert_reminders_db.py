"""Epic 007, sub-plan 4.2, T-2.3 against a real database.

C-6: alert rows stay out of reminders' list and search. C-7: an alert fires
once as an ``event_alert`` notification whose target is the event and whose
action target is its row, and Done from the panel acts on that row. The
replace and clear run as one set each (AD-8). Rule T7: user B's calls touch
none of user A's alerts.
"""

import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql import text

from app.core import auth as auth_module
from app.core.context import Context
from app.core.db import user_transaction
from app.core.deps import build_fire_one_interactor, build_reminder_service
from app.core.settings import Settings
from app.domains.reminders.public import AlertNotSet, EventAlertRequest, ReminderService
from app.domains.reminders.repositories.reminder_repository import (
    SqlReminderRepository,
)

ALGORITHM = "ES256"
INSERT_EVENT = text(
    "INSERT INTO calendar_events (id, user_id, title, start_date, "
    "schedule_timezone, starts_at, ends_at, alert_leads_minutes, origin, "
    "created_at, updated_at) VALUES (:id, :user_id, 'Flight to Delhi', "
    ":start_date, 'Asia/Kolkata', :starts_at, :starts_at, '{60, 1440}', "
    "'command', now(), now())"
)
LIVE_ALERTS = text(
    "SELECT next_fire_at FROM reminders WHERE event_id = :event_id "
    "AND deleted_at IS NULL ORDER BY next_fire_at"
)
EVENT_NOTIFICATIONS = text(
    "SELECT kind::text, target_id, action_target_id, title, detail, action::text, "
    "deleted_at FROM notifications WHERE target_id = :event_id"
)


@pytest.fixture
def signing_key() -> ec.EllipticCurvePrivateKey:
    return ec.generate_private_key(ec.SECP256R1())


@pytest.fixture
def patched_jwks(
    monkeypatch: pytest.MonkeyPatch, signing_key: ec.EllipticCurvePrivateKey
) -> None:
    class FakeKey:
        key = signing_key.public_key()

    class FakeClient:
        def get_signing_key_from_jwt(self, _token: str) -> FakeKey:
            return FakeKey()

    monkeypatch.setattr(auth_module, "_get_jwks_client", lambda _s: FakeClient())


def _headers(
    key: ec.EllipticCurvePrivateKey, settings: Settings, *, user_id: uuid.UUID
) -> dict[str, str]:
    claims: dict[str, Any] = {
        "sub": str(user_id),
        "iss": settings.jwt_issuer,
        "exp": datetime.now(UTC) + timedelta(hours=1),
    }
    return {"Authorization": f"Bearer {jwt.encode(claims, key, algorithm=ALGORITHM)}"}


# One instant for the whole module, so two reads of "in five days" agree.
_BASE = datetime.now(UTC).replace(microsecond=0)


def _in_days(days: int) -> datetime:
    return _BASE + timedelta(days=days)


async def _insert_event(
    session_factory: async_sessionmaker[AsyncSession], *, user_id: uuid.UUID
) -> uuid.UUID:
    event_id = uuid.uuid4()
    async with (
        session_factory() as session,
        user_transaction(session, user_id) as scoped,
    ):
        await scoped.execute(
            INSERT_EVENT,
            {
                "id": event_id,
                "user_id": user_id,
                "start_date": date.today() + timedelta(days=10),
                "starts_at": _in_days(10),
            },
        )
    return event_id


def _reminder_service(
    *,
    session: AsyncSession,
    session_factory: async_sessionmaker[AsyncSession],
    user_id: uuid.UUID,
) -> ReminderService:
    """Wired as a request wires it, so the adapters are the real ones."""
    return build_reminder_service(
        Context(
            user_id=user_id,
            email=None,
            session=session,
            request_id="test",
            session_factory=session_factory,
        )
    )


async def _set_alerts(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    user_id: uuid.UUID,
    event_id: uuid.UUID,
    fire_times: list[datetime],
) -> list[AlertNotSet]:
    async with session_factory() as session:
        return await _reminder_service(
            session=session, session_factory=session_factory, user_id=user_id
        ).set_event_alerts(
            user_id=user_id,
            event_id=event_id,
            title="Flight to Delhi",
            alerts=[
                EventAlertRequest(fires_at=fires_at, detail="1 day before")
                for fires_at in fire_times
            ],
            origin="command",
            now=datetime.now(UTC),
        )


async def _clear_alerts(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    user_id: uuid.UUID,
    event_id: uuid.UUID,
) -> None:
    async with session_factory() as session:
        await _reminder_service(
            session=session, session_factory=session_factory, user_id=user_id
        ).clear_event_alerts(user_id=user_id, event_id=event_id)


async def _live_alerts(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    user_id: uuid.UUID,
    event_id: uuid.UUID,
) -> list[datetime]:
    async with (
        session_factory() as session,
        user_transaction(session, user_id) as scoped,
    ):
        return list((await scoped.scalars(LIVE_ALERTS, {"event_id": event_id})).all())


async def test_setting_again_replaces_the_rows_as_one_set(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """AD-8, FR-21: the old rows are soft-deleted, the new ones live."""
    user_a, _ = two_users
    event_id = await _insert_event(session_factory, user_id=user_a)
    await _set_alerts(
        session_factory,
        user_id=user_a,
        event_id=event_id,
        fire_times=[_in_days(3), _in_days(9)],
    )

    not_set = await _set_alerts(
        session_factory, user_id=user_a, event_id=event_id, fire_times=[_in_days(5)]
    )

    assert not_set == []
    assert await _live_alerts(session_factory, user_id=user_a, event_id=event_id) == [
        _in_days(5)
    ]


async def test_alert_rows_stay_out_of_reminders_list_and_search(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-6, FR-32, while the cap still counts them (FR-33)."""
    user_a, _ = two_users
    event_id = await _insert_event(session_factory, user_id=user_a)
    await _set_alerts(
        session_factory, user_id=user_a, event_id=event_id, fire_times=[_in_days(3)]
    )

    async with session_factory() as session:
        repository = SqlReminderRepository(session)
        listed = await repository.list_for_user(user_id=user_a)
        found = await repository.search_reminders(
            user_id=user_a,
            terms=["delhi"],
            query_embedding=None,
            max_distance=0.5,
            limit=10,
        )
        active_count = await repository.count_active_for_user(user_id=user_a)

    assert listed == []
    assert found.total == 0
    assert active_count == 1


async def test_an_alert_fires_once_as_an_event_alert_and_done_acts_on_its_row(
    client: AsyncClient,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-7, FR-17, FR-18, AD-5 and 4.2 Q2."""
    user_a, _ = two_users
    event_id = await _insert_event(session_factory, user_id=user_a)
    fires_at = _in_days(3)
    await _set_alerts(
        session_factory, user_id=user_a, event_id=event_id, fire_times=[fires_at]
    )
    async with (
        session_factory() as session,
        user_transaction(session, user_a) as scoped,
    ):
        alert_id = await scoped.scalar(
            text("SELECT id FROM reminders WHERE event_id = :event_id"),
            {"event_id": event_id},
        )

    for _ in range(2):
        async with session_factory() as session:
            await build_fire_one_interactor(session).fire_one(
                reminder_id=alert_id, scheduled_for=fires_at
            )
    done = await client.post(
        "/graphql",
        json={
            "query": "mutation($id: ID!) { markReminderDone(id: $id) { __typename } }",
            "variables": {"id": str(alert_id)},
        },
        headers=_headers(signing_key, settings, user_id=user_a),
    )
    async with (
        session_factory() as session,
        user_transaction(session, user_a) as scoped,
    ):
        notifications = (
            await scoped.execute(EVENT_NOTIFICATIONS, {"event_id": event_id})
        ).all()

    assert done.json()["data"]["markReminderDone"]["__typename"] == "Reminder"
    [notification] = notifications
    assert notification.kind == "event_alert"
    assert notification.action_target_id == alert_id
    assert (notification.title, notification.detail) == (
        "Flight to Delhi",
        "1 day before",
    )
    assert notification.action == "done"


async def test_clearing_ends_every_alert_and_hides_their_notifications(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """FR-23."""
    user_a, _ = two_users
    event_id = await _insert_event(session_factory, user_id=user_a)
    fires_at = _in_days(3)
    await _set_alerts(
        session_factory,
        user_id=user_a,
        event_id=event_id,
        fire_times=[fires_at, _in_days(9)],
    )
    async with (
        session_factory() as session,
        user_transaction(session, user_a) as scoped,
    ):
        alert_id = await scoped.scalar(
            text(
                "SELECT id FROM reminders WHERE event_id = :event_id "
                "ORDER BY next_fire_at LIMIT 1"
            ),
            {"event_id": event_id},
        )
    async with session_factory() as session:
        await build_fire_one_interactor(session).fire_one(
            reminder_id=alert_id, scheduled_for=fires_at
        )

    await _clear_alerts(session_factory, user_id=user_a, event_id=event_id)

    async with (
        session_factory() as session,
        user_transaction(session, user_a) as scoped,
    ):
        notifications = (
            await scoped.execute(EVENT_NOTIFICATIONS, {"event_id": event_id})
        ).all()
    assert await _live_alerts(session_factory, user_id=user_a, event_id=event_id) == []
    assert [notification.deleted_at is not None for notification in notifications] == [
        True
    ]


async def test_another_user_cannot_clear_or_replace_an_events_alerts(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """Rule T7: user B's calls with user A's event id change nothing of A's."""
    user_a, user_b = two_users
    event_id = await _insert_event(session_factory, user_id=user_a)
    await _set_alerts(
        session_factory, user_id=user_a, event_id=event_id, fire_times=[_in_days(3)]
    )

    await _clear_alerts(session_factory, user_id=user_b, event_id=event_id)

    assert await _live_alerts(session_factory, user_id=user_a, event_id=event_id) == [
        _in_days(3)
    ]
