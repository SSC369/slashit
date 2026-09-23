"""Slice 2 against a real database: firing writes one firing and one
notification (TC-2.5), the sweep queues each occurrence once (TC-2.11), the
panel's queries and mutations (TC-2.12), user B can touch none of user A's
rows (TC-2.13, rule T7), and a NOTIFY reaches the listener (TC-2.15)."""

import asyncio
import uuid
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql import text

from app.core import auth as auth_module
from app.core.db import user_transaction
from app.core.deps import build_fire_due_interactor, build_fire_one_interactor
from app.core.jobs import procrastinate_app
from app.core.settings import Settings
from app.domains.notifications.services.live_signal import LiveSignal

ALGORITHM = "ES256"

INSERT_DUE_REMINDER = text(
    "INSERT INTO reminders (id, user_id, description, repeat_kind, repeat_interval, "
    "repeat_weekdays, local_time, anchor_local_date, one_time_at, next_fire_at, "
    "schedule_timezone, state, origin, created_at, updated_at) VALUES "
    "(:id, :user_id, :description, 'none', 1, '{}', :local_time, :anchor, "
    ":fire_at, :fire_at, 'Asia/Kolkata', 'upcoming', 'command', now(), now())"
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


async def _seed_due(
    session_factory: async_sessionmaker[AsyncSession], *, user_id: uuid.UUID
) -> tuple[uuid.UUID, datetime]:
    reminder_id = uuid.uuid4()
    fire_at = datetime.now(UTC).replace(microsecond=0) - timedelta(seconds=30)
    async with session_factory() as session, user_transaction(session, user_id) as s:
        await s.execute(
            INSERT_DUE_REMINDER,
            {
                "id": reminder_id,
                "user_id": user_id,
                "description": "Call Mom",
                "local_time": time(19),
                "anchor": date.today(),
                "fire_at": fire_at,
            },
        )
    return reminder_id, fire_at


async def _fire(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    reminder_id: uuid.UUID,
    scheduled_for: datetime,
) -> str:
    """As the worker does: a service-role session, no request identity."""
    async with session_factory() as session:
        return await build_fire_one_interactor(session).fire_one(
            reminder_id=reminder_id, scheduled_for=scheduled_for
        )


async def _graphql(
    client: AsyncClient, *, query: str, headers: dict[str, str], **variables: Any
) -> dict[str, Any]:
    response = await client.post(
        "/graphql", json={"query": query, "variables": variables}, headers=headers
    )
    body: dict[str, Any] = response.json()
    assert response.status_code == 200, body
    assert "errors" not in body, body
    result: dict[str, Any] = body["data"]
    return result


# Two root fields in one document would resolve concurrently on the request's
# one session, which it does not allow (dev log). The client sends them apart.
PANEL_QUERY = """
query {
  notifications {
    items { id title marker showPopup read targetId action }
    nextCursor
  }
}
"""
COUNT_QUERY = "query { unreadNotificationCount }"


async def test_firing_twice_writes_one_firing_and_one_notification(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """TC-2.5, FR-16, NFR-3."""
    user_a, _ = two_users
    reminder_id, fire_at = await _seed_due(session_factory, user_id=user_a)

    first = await _fire(session_factory, reminder_id=reminder_id, scheduled_for=fire_at)
    second = await _fire(
        session_factory, reminder_id=reminder_id, scheduled_for=fire_at
    )

    async with session_factory() as session:
        counts = (
            await session.execute(
                text(
                    "SELECT (SELECT count(*) FROM reminder_firings "
                    "        WHERE reminder_id = :id), "
                    "       (SELECT count(*) FROM notifications "
                    "        WHERE target_id = :id), "
                    "       (SELECT state::text FROM reminders WHERE id = :id)"
                ),
                {"id": reminder_id},
            )
        ).one()
    assert (first, second) == ("fired", "skipped")
    assert tuple(counts) == (1, 1, "fired")


async def test_two_sweeps_queue_one_job_per_occurrence(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """TC-2.11, X-4, AD-2: the queueing lock holds against the real queue."""
    user_a, _ = two_users
    reminder_id, _ = await _seed_due(session_factory, user_id=user_a)
    lock_prefix = f"fire:{reminder_id}:%"

    async with procrastinate_app.open_async():
        async with session_factory() as session:
            await build_fire_due_interactor(session).fire_due()
            await build_fire_due_interactor(session).fire_due()
        async with session_factory() as session:
            queued = await session.scalar(
                text(
                    "SELECT count(*) FROM procrastinate.procrastinate_jobs "
                    "WHERE queueing_lock LIKE :lock"
                ),
                {"lock": lock_prefix},
            )
            # The queue's triggers name its tables unqualified, as its own
            # connections see them (migration 0020).
            await session.execute(text("SET LOCAL search_path TO procrastinate"))
            await session.execute(
                text(
                    "DELETE FROM procrastinate.procrastinate_jobs "
                    "WHERE queueing_lock LIKE :lock"
                ),
                {"lock": lock_prefix},
            )
            await session.commit()
    assert queued == 1


async def test_the_panel_lists_counts_and_marks_read(
    client: AsyncClient,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """TC-2.12, FR-35 to FR-37."""
    user_a, _ = two_users
    headers = _headers(signing_key, settings, user_id=user_a)
    reminder_id, fire_at = await _seed_due(session_factory, user_id=user_a)
    await _fire(session_factory, reminder_id=reminder_id, scheduled_for=fire_at)

    before = await _graphql(client, query=PANEL_QUERY, headers=headers)
    count_before = await _graphql(client, query=COUNT_QUERY, headers=headers)
    [item] = before["notifications"]["items"]
    read = await _graphql(
        client,
        query="mutation($id: ID!) { markNotificationRead(id: $id) { "
        "__typename ... on Notification { read } } }",
        headers=headers,
        id=item["id"],
    )
    count_after = await _graphql(client, query=COUNT_QUERY, headers=headers)

    assert count_before["unreadNotificationCount"] == 1
    assert item["title"] == "Call Mom"
    assert item["marker"] == "NONE"
    assert item["showPopup"] is True
    assert item["targetId"] == str(reminder_id)
    assert read["markNotificationRead"] == {"__typename": "Notification", "read": True}
    assert count_after["unreadNotificationCount"] == 0


async def test_done_from_the_panel_closes_the_reminder_and_stamps_the_item(
    client: AsyncClient,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """FR-19 over the wire; the panel then reads "marked done"."""
    user_a, _ = two_users
    headers = _headers(signing_key, settings, user_id=user_a)
    reminder_id, fire_at = await _seed_due(session_factory, user_id=user_a)
    await _fire(session_factory, reminder_id=reminder_id, scheduled_for=fire_at)

    done = await _graphql(
        client,
        query="mutation($id: ID!) { markReminderDone(id: $id) { "
        "__typename ... on Reminder { state } } }",
        headers=headers,
        id=str(reminder_id),
    )
    panel = await _graphql(client, query=PANEL_QUERY, headers=headers)

    assert done["markReminderDone"] == {"__typename": "Reminder", "state": "DONE"}
    [item] = panel["notifications"]["items"]
    assert (item["action"], item["read"]) == ("DONE", True)


async def test_another_user_cannot_touch_a_firing_or_its_notification(
    client: AsyncClient,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """TC-2.13, NFR-6, rule T7."""
    user_a, user_b = two_users
    reminder_id, fire_at = await _seed_due(session_factory, user_id=user_a)
    await _fire(session_factory, reminder_id=reminder_id, scheduled_for=fire_at)
    a_panel = await _graphql(
        client,
        query=PANEL_QUERY,
        headers=_headers(signing_key, settings, user_id=user_a),
    )
    notification_id = a_panel["notifications"]["items"][0]["id"]
    b_headers = _headers(signing_key, settings, user_id=user_b)

    b_panel = await _graphql(client, query=PANEL_QUERY, headers=b_headers)
    b_count = await _graphql(client, query=COUNT_QUERY, headers=b_headers)
    b_read = await _graphql(
        client,
        query="mutation($id: ID!) { markNotificationRead(id: $id) { __typename } }",
        headers=b_headers,
        id=notification_id,
    )
    b_done = await _graphql(
        client,
        query="mutation($id: ID!) { markReminderDone(id: $id) { __typename } }",
        headers=b_headers,
        id=str(reminder_id),
    )
    b_snooze = await _graphql(
        client,
        query="mutation($id: ID!) { snoozeReminder(id: $id, option: ONE_HOUR) "
        "{ __typename } }",
        headers=b_headers,
        id=str(reminder_id),
    )
    b_all = await _graphql(
        client,
        query="mutation { markAllNotificationsRead { markedCount } }",
        headers=b_headers,
    )
    a_after = await _graphql(
        client,
        query=COUNT_QUERY,
        headers=_headers(signing_key, settings, user_id=user_a),
    )

    assert b_count["unreadNotificationCount"] == 0
    assert b_panel["notifications"]["items"] == []
    assert b_read["markNotificationRead"]["__typename"] == "NotificationNotFound"
    assert b_done["markReminderDone"]["__typename"] == "ReminderNotFound"
    assert b_snooze["snoozeReminder"]["__typename"] == "ReminderNotFound"
    assert b_all["markAllNotificationsRead"]["markedCount"] == 0
    assert a_after["unreadNotificationCount"] == 1


async def test_a_firing_reaches_the_listener_through_notify(
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """TC-2.15, AD-4: the NOTIFY leaves at commit and reaches only its user."""
    user_a, user_b = two_users
    signal = LiveSignal(channel="slashit_notifications")
    await signal.start(dsn=settings.database_url)
    try:
        async with (
            signal.subscribe(user_id=user_a) as a_feed,
            signal.subscribe(user_id=user_b) as b_feed,
        ):
            await asyncio.sleep(0.5)  # let the LISTEN connection open
            reminder_id, fire_at = await _seed_due(session_factory, user_id=user_a)
            await _fire(session_factory, reminder_id=reminder_id, scheduled_for=fire_at)
            received_id = await asyncio.wait_for(a_feed.next_notification_id(), 5)
            assert b_feed.queue.empty()
    finally:
        await signal.stop()

    async with session_factory() as session:
        target_id = await session.scalar(
            text("SELECT target_id FROM notifications WHERE id = :id"),
            {"id": received_id},
        )
    assert target_id == reminder_id
