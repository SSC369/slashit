"""Epic 007, sub-plan 4.2, T-2.9: rule T7 over the slice's remaining paths.

User B never sees, acts on or moves anything of user A's: A's fired event
alert is not in B's panel, and B's Done or Snooze on A's alert row is
`ReminderNotFound`; B's timezone change moves none of A's events. Edit,
delete, search, related, the sweep and the alert set and clear have their
own T7 cases beside their tasks (C-17).
"""

import uuid
from datetime import UTC, datetime, time, timedelta
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
from app.core.deps import (
    build_event_service,
    build_fire_one_interactor,
    build_rezone_events_interactor,
)
from app.core.settings import Settings
from app.domains.events.public import EventDTO, EventFields

PANEL = "query { notifications { items { id kind targetId actionTargetId } } }"


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


async def _graphql(
    client: AsyncClient, *, query: str, headers: dict[str, str], **variables: Any
) -> dict[str, Any]:
    response = await client.post(
        "/graphql", json={"query": query, "variables": variables}, headers=headers
    )
    body: dict[str, Any] = response.json()
    assert "errors" not in body, body
    data: dict[str, Any] = body["data"]
    return data


async def _create(
    session_factory: async_sessionmaker[AsyncSession], *, user_id: uuid.UUID
) -> EventDTO:
    async with session_factory() as session:
        event = await build_event_service(
            Context(
                user_id=user_id,
                email=None,
                session=session,
                request_id="test",
                session_factory=session_factory,
            )
        ).create_event(
            user_id=user_id,
            fields=EventFields(
                title="Dentist",
                start_date=datetime.now(UTC).date() + timedelta(days=10),
                has_year=True,
                start_time=time(16),
                end_date=None,
                end_time=None,
                location=None,
                description=None,
                repeat_yearly=False,
                alert_leads_minutes=(1440,),
            ),
            origin="command",
            original_input=None,
        )
    assert isinstance(event, EventDTO)
    return event


async def test_user_b_cannot_see_or_act_on_user_as_event_alert(
    client: AsyncClient,
    signing_key: ec.EllipticCurvePrivateKey,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    user_a, user_b = two_users
    event = await _create(session_factory, user_id=user_a)
    async with (
        session_factory() as session,
        user_transaction(session, user_a) as scoped,
    ):
        alert = (
            await scoped.execute(
                text("SELECT id, next_fire_at FROM reminders WHERE event_id = :id"),
                {"id": event.id},
            )
        ).one()
    async with session_factory() as session:
        await build_fire_one_interactor(session).fire_one(
            reminder_id=alert.id, scheduled_for=alert.next_fire_at
        )
    headers_b = _headers(signing_key, settings, user_id=user_b)

    panel_a = await _graphql(
        client,
        query=PANEL,
        headers=_headers(signing_key, settings, user_id=user_a),
    )
    panel_b = await _graphql(client, query=PANEL, headers=headers_b)
    done_b = await _graphql(
        client,
        query="mutation($id: ID!) { markReminderDone(id: $id) { __typename } }",
        headers=headers_b,
        id=str(alert.id),
    )
    snooze_b = await _graphql(
        client,
        query="mutation($id: ID!) { snoozeReminder(id: $id, option: ONE_HOUR) "
        "{ __typename } }",
        headers=headers_b,
        id=str(alert.id),
    )

    assert panel_a["notifications"]["items"][0]["kind"] == "EVENT_ALERT"
    assert panel_a["notifications"]["items"][0]["targetId"] == str(event.id)
    assert panel_a["notifications"]["items"][0]["actionTargetId"] == str(alert.id)
    assert panel_b["notifications"]["items"] == []
    assert done_b["markReminderDone"]["__typename"] == "ReminderNotFound"
    assert snooze_b["snoozeReminder"]["__typename"] == "ReminderNotFound"


async def test_user_bs_timezone_job_moves_none_of_user_as_events(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    user_a, user_b = two_users
    event = await _create(session_factory, user_id=user_a)
    async with (
        session_factory() as session,
        user_transaction(session, user_b) as scoped,
    ):
        await scoped.execute(
            text(
                "INSERT INTO user_settings (user_id, timezone, created_at, "
                "updated_at) VALUES (:user_id, 'Pacific/Pago_Pago', now(), now()) "
                "ON CONFLICT (user_id) DO UPDATE SET timezone = EXCLUDED.timezone"
            ),
            {"user_id": user_b},
        )

    async with session_factory() as session:
        moved = await build_rezone_events_interactor(
            session=session, session_factory=session_factory
        ).rezone_events(user_id=user_b)

    async with (
        session_factory() as session,
        user_transaction(session, user_a) as scoped,
    ):
        zone = await scoped.scalar(
            text("SELECT schedule_timezone FROM calendar_events WHERE id = :id"),
            {"id": event.id},
        )
    assert moved == 0
    assert zone == event.schedule.timezone
