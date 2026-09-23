"""The live feed over a real WebSocket: TC-2.15 end to end, and the token in
`connection_init` that a browser must use, since it cannot set headers."""

import asyncio
import time as wall_clock
import uuid
from datetime import UTC, date, datetime, time, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from sqlalchemy.sql import text
from starlette.testclient import TestClient

from app.core import auth as auth_module
from app.core.db import create_engine, create_session_factory, user_transaction
from app.core.deps import build_fire_one_interactor
from app.core.settings import Settings, get_settings
from app.main import create_app

PROTOCOL = "graphql-transport-ws"
SUBSCRIPTION = "subscription { notificationReceived { title targetId showPopup } }"


@pytest.fixture
def signing_key(monkeypatch: pytest.MonkeyPatch) -> ec.EllipticCurvePrivateKey:
    signing_key = ec.generate_private_key(ec.SECP256R1())
    public_key = signing_key.public_key()

    class FakeKey:
        key = public_key

    class FakeClient:
        def get_signing_key_from_jwt(self, _token: str) -> FakeKey:
            return FakeKey()

    monkeypatch.setattr(auth_module, "_get_jwks_client", lambda _s: FakeClient())
    return signing_key


def _token(
    key: ec.EllipticCurvePrivateKey, settings: Settings, user_id: uuid.UUID
) -> str:
    claims = {
        "sub": str(user_id),
        "iss": settings.jwt_issuer,
        "exp": datetime.now(UTC) + timedelta(hours=1),
    }
    return jwt.encode(claims, key, algorithm="ES256")


async def _with_user_and_firing(settings: Settings, user_id: uuid.UUID) -> uuid.UUID:
    """Seed a due reminder for a fresh user and fire it, as the worker does."""
    engine = create_engine(settings)
    session_factory = create_session_factory(engine)
    reminder_id = uuid.uuid4()
    fire_at = datetime.now(UTC).replace(microsecond=0) - timedelta(seconds=10)
    try:
        async with (
            session_factory() as session,
            user_transaction(session, user_id) as s,
        ):
            await s.execute(
                text(
                    "INSERT INTO reminders (id, user_id, description, repeat_kind, "
                    "repeat_interval, repeat_weekdays, local_time, anchor_local_date, "
                    "one_time_at, next_fire_at, schedule_timezone, state, origin, "
                    "created_at, updated_at) VALUES (:id, :user_id, 'Call Mom', "
                    "'none', 1, '{}', :local_time, :anchor, :fire_at, :fire_at, "
                    "'Asia/Kolkata', 'upcoming', 'command', now(), now())"
                ),
                {
                    "id": reminder_id,
                    "user_id": user_id,
                    "local_time": time(19),
                    "anchor": date.today(),
                    "fire_at": fire_at,
                },
            )
        async with session_factory() as session:
            await build_fire_one_interactor(session).fire_one(
                reminder_id=reminder_id, scheduled_for=fire_at
            )
    finally:
        await engine.dispose()
    return reminder_id


async def _add_user(settings: Settings, user_id: uuid.UUID) -> None:
    engine = create_engine(settings)
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO auth.users (id, email, instance_id) VALUES "
                    "(:id, :email, '00000000-0000-0000-0000-000000000000')"
                ),
                {"id": user_id, "email": f"{user_id}@ws-test.invalid"},
            )
    finally:
        await engine.dispose()


async def _remove_user(settings: Settings, user_id: uuid.UUID) -> None:
    engine = create_engine(settings)
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM auth.users WHERE id = :id"), {"id": user_id}
            )
    finally:
        await engine.dispose()


def test_a_fired_reminder_arrives_over_the_websocket(
    signing_key: ec.EllipticCurvePrivateKey,
) -> None:
    settings = get_settings()
    user_id = uuid.uuid4()
    asyncio.run(_add_user(settings, user_id))
    try:
        with (
            TestClient(create_app(settings)) as client,
            client.websocket_connect("/graphql", subprotocols=[PROTOCOL]) as socket,
        ):
            bearer = f"Bearer {_token(signing_key, settings, user_id)}"
            socket.send_json(
                {"type": "connection_init", "payload": {"authorization": bearer}}
            )
            assert socket.receive_json()["type"] == "connection_ack"
            socket.send_json(
                {"id": "1", "type": "subscribe", "payload": {"query": SUBSCRIPTION}}
            )
            wall_clock.sleep(1.0)  # the subscription and the LISTEN connection open
            reminder_id = asyncio.run(_with_user_and_firing(settings, user_id))
            message = socket.receive_json()
        assert message["type"] == "next"
        assert message["payload"]["data"]["notificationReceived"] == {
            "title": "Call Mom",
            "targetId": str(reminder_id),
            "showPopup": True,
        }
    finally:
        asyncio.run(_remove_user(settings, user_id))


def test_a_bad_token_is_refused_at_connection_init(
    signing_key: ec.EllipticCurvePrivateKey,
) -> None:
    settings = get_settings()
    with (
        TestClient(create_app(settings)) as client,
        client.websocket_connect("/graphql", subprotocols=[PROTOCOL]) as socket,
    ):
        socket.send_json(
            {"type": "connection_init", "payload": {"authorization": "Bearer nonsense"}}
        )
        closed = socket.receive()
    assert closed["type"] == "websocket.close"
    assert closed["code"] == 4403
