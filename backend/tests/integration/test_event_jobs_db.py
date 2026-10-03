"""Epic 007, sub-plan 4.2, T-2.6 against a real database and job queue.

A timezone change queues events' own job beside reminders' (identity defers
both by name), and that job moves an all-day event and its alert to the new
zone (C-14). The 15-minute sweep, on the service role, rolls one user's
ended yearly event and arms another user's pending event, touching nothing
else of theirs (C-11, C-12, rule T7).
"""

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
from app.core.context import Context
from app.core.db import user_transaction
from app.core.deps import (
    build_event_service,
    build_rezone_events_interactor,
    build_roll_yearly_interactor,
)
from app.core.settings import Settings
from app.domains.events.public import EventDTO, EventFields

UPDATE_TIMEZONE = """
mutation($input: UpdateTimezoneInput!) {
  updateTimezone(input: $input) { __typename ... on Settings { timezone } }
}
"""
EVENT_ROW = text(
    "SELECT starts_at, schedule_timezone, alerts_pending FROM calendar_events "
    "WHERE id = :id"
)
LIVE_ALERTS = text(
    "SELECT next_fire_at FROM reminders WHERE event_id = :event_id "
    "AND deleted_at IS NULL ORDER BY next_fire_at"
)


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


async def _create(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    user_id: uuid.UUID,
    start_date: date,
    repeat_yearly: bool,
) -> EventDTO:
    async with session_factory() as session:
        outcome = await build_event_service(
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
                title="Mom's birthday",
                start_date=start_date,
                has_year=True,
                start_time=None,
                end_date=None,
                end_time=None,
                location=None,
                description=None,
                repeat_yearly=repeat_yearly,
                alert_leads_minutes=(1440,),
            ),
            origin="command",
            original_input=None,
        )
    assert isinstance(outcome, EventDTO)
    return outcome


async def _execute(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    user_id: uuid.UUID,
    sql: str,
    **params: Any,
) -> None:
    async with (
        session_factory() as session,
        user_transaction(session, user_id) as scoped,
    ):
        await scoped.execute(text(sql), params)


async def _event_row(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    user_id: uuid.UUID,
    event_id: uuid.UUID,
) -> Any:
    async with (
        session_factory() as session,
        user_transaction(session, user_id) as scoped,
    ):
        return (await scoped.execute(EVENT_ROW, {"id": event_id})).one()


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


async def test_a_timezone_change_queues_and_runs_events_own_job(
    client: AsyncClient,
    signing_key: ec.EllipticCurvePrivateKey,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
    job_queue: None,
) -> None:
    """C-14 and AD-6: one job per task; the all-day event keeps its date."""
    user_a, _ = two_users
    start_date = datetime.now(UTC).date() + timedelta(days=20)
    event = await _create(
        session_factory, user_id=user_a, start_date=start_date, repeat_yearly=False
    )

    response = await client.post(
        "/graphql",
        json={
            "query": UPDATE_TIMEZONE,
            "variables": {"input": {"timezone": "Pacific/Pago_Pago"}},
        },
        headers=_headers(signing_key, settings, user_id=user_a),
    )
    async with session_factory() as session:
        queued_tasks = (
            await session.scalars(
                text(
                    "SELECT task_name FROM procrastinate.procrastinate_jobs "
                    "WHERE queueing_lock = ANY(:locks) ORDER BY task_name"
                ),
                {"locks": [f"tz:{user_a}", f"events-tz:{user_a}"]},
            )
        ).all()
    async with session_factory() as session:
        moved = await build_rezone_events_interactor(
            session=session, session_factory=session_factory
        ).rezone_events(user_id=user_a)

    row = await _event_row(session_factory, user_id=user_a, event_id=event.id)
    assert response.json()["data"]["updateTimezone"]["timezone"] == "Pacific/Pago_Pago"
    assert queued_tasks == ["events.timezone_changed", "reminders.timezone_changed"]
    assert moved == 1
    assert row.schedule_timezone == "Pacific/Pago_Pago"
    assert row.alerts_pending is False
    # Pago Pago is UTC-11 all year, so local midnight is 11:00 UTC.
    assert row.starts_at.astimezone(UTC) == (
        datetime.combine(start_date, time(0), tzinfo=UTC) + timedelta(hours=11)
    )
    assert await _live_alerts(session_factory, user_id=user_a, event_id=event.id) == [
        datetime.combine(start_date - timedelta(days=1), time(9), tzinfo=UTC)
        + timedelta(hours=11)
    ]


async def test_the_sweep_rolls_one_users_event_and_arms_anothers(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-11, C-12 and T7 on the service role."""
    user_a, user_b = two_users
    today = datetime.now(UTC).date()
    yearly = await _create(
        session_factory,
        user_id=user_a,
        start_date=today + timedelta(days=30),
        repeat_yearly=True,
    )
    pending = await _create(
        session_factory,
        user_id=user_b,
        start_date=today + timedelta(days=30),
        repeat_yearly=False,
    )
    ended_at = datetime.now(UTC) - timedelta(days=1)
    await _execute(
        session_factory,
        user_id=user_a,
        sql="UPDATE calendar_events SET starts_at = :ended, ends_at = :ended "
        "WHERE id = :id",
        ended=ended_at,
        id=yearly.id,
    )
    await _execute(
        session_factory,
        user_id=user_b,
        sql="UPDATE reminders SET deleted_at = now() WHERE event_id = :id",
        id=pending.id,
    )
    await _execute(
        session_factory,
        user_id=user_b,
        sql="UPDATE calendar_events SET alerts_pending = true, "
        "updated_at = now() - interval '10 minutes' WHERE id = :id",
        id=pending.id,
    )

    async with session_factory() as session:
        counts = await build_roll_yearly_interactor(
            session=session, session_factory=session_factory
        ).roll_yearly()

    rolled = await _event_row(session_factory, user_id=user_a, event_id=yearly.id)
    repaired = await _event_row(session_factory, user_id=user_b, event_id=pending.id)
    assert counts.rolled >= 1
    assert counts.repaired >= 1
    assert rolled.starts_at > datetime.now(UTC)
    assert rolled.alerts_pending is False
    assert repaired.alerts_pending is False
    assert (
        len(await _live_alerts(session_factory, user_id=user_b, event_id=pending.id))
        == 1
    )
    assert (
        len(await _live_alerts(session_factory, user_id=user_a, event_id=yearly.id))
        == 1
    )
