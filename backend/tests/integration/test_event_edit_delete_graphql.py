"""Epic 007, sub-plan 4.2, T-2.5 over the wire, against a real database.

`updateEvent` and `deleteEvent` through GraphQL, with the real reminders
behind them: every union member is produced (repo-rules.md section 15), an
edit moves the alert rows (C-8), a delete ends them (C-10), and user B gets
`EventNotFound` for user A's event (C-17, rule T7).
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
from app.core.deps import build_event_service
from app.core.settings import Settings
from app.domains.events.public import EventDTO, EventFields

ALGORITHM = "ES256"
UPDATE = """
mutation($id: ID!, $input: EventInput!) {
  updateEvent(id: $id, input: $input) {
    __typename
    ... on EventUpdated {
      event { title alerts { leadMinutes text } }
      alertsNotSet { leadMinutes reason }
    }
    ... on EventInvalid { field reason message }
    ... on EventNotFound { message }
  }
}
"""
DELETE = """
mutation($id: ID!) {
  deleteEvent(id: $id) { __typename ... on EventDeleted { id } }
}
"""
LIVE_ALERTS = text(
    "SELECT next_fire_at FROM reminders WHERE event_id = :event_id "
    "AND deleted_at IS NULL ORDER BY next_fire_at"
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


async def _create_event(
    session_factory: async_sessionmaker[AsyncSession], *, user_id: uuid.UUID
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
            original_input="/add-event Dentist",
        )
    assert isinstance(outcome, EventDTO)
    return outcome


def _input(*, days_ahead: int, title: str = "Dentist") -> dict[str, Any]:
    return {
        "title": title,
        "location": None,
        "description": None,
        "startDate": (
            datetime.now(UTC).date() + timedelta(days=days_ahead)
        ).isoformat(),
        "startTime": "16:00",
        "endDate": None,
        "endTime": None,
        "repeatYearly": False,
        "alertLeadsMinutes": [60, 1440],
    }


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


async def test_an_edit_moves_and_adds_alerts(
    client: AsyncClient,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-8 and C-9: `EventUpdated`, with the rows replaced as a set."""
    user_a, _ = two_users
    event = await _create_event(session_factory, user_id=user_a)

    data = await _graphql(
        client,
        query=UPDATE,
        headers=_headers(signing_key, settings, user_id=user_a),
        id=str(event.id),
        input=_input(days_ahead=12),
    )

    result = data["updateEvent"]
    assert result["__typename"] == "EventUpdated"
    assert [alert["text"] for alert in result["event"]["alerts"]] == [
        "1 day before",
        "1 hour before",
    ]
    assert result["alertsNotSet"] == []
    assert (
        len(await _live_alerts(session_factory, user_id=user_a, event_id=event.id)) == 2
    )


async def test_an_end_before_the_start_is_event_invalid(
    client: AsyncClient,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    user_a, _ = two_users
    event = await _create_event(session_factory, user_id=user_a)
    edit = _input(days_ahead=12)
    edit["endDate"] = (datetime.now(UTC).date() + timedelta(days=11)).isoformat()

    data = await _graphql(
        client,
        query=UPDATE,
        headers=_headers(signing_key, settings, user_id=user_a),
        id=str(event.id),
        input=edit,
    )

    assert data["updateEvent"]["__typename"] == "EventInvalid"
    assert data["updateEvent"]["field"] == "END"
    assert data["updateEvent"]["reason"] == "END_BEFORE_START"


async def test_a_delete_ends_every_alert(
    client: AsyncClient,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-10, FR-23, FR-29: `EventDeleted`."""
    user_a, _ = two_users
    event = await _create_event(session_factory, user_id=user_a)
    headers = _headers(signing_key, settings, user_id=user_a)

    data = await _graphql(client, query=DELETE, headers=headers, id=str(event.id))
    again = await _graphql(client, query=DELETE, headers=headers, id=str(event.id))

    assert data["deleteEvent"] == {"__typename": "EventDeleted", "id": str(event.id)}
    assert again["deleteEvent"]["__typename"] == "EventNotFound"
    assert await _live_alerts(session_factory, user_id=user_a, event_id=event.id) == []


async def test_user_b_cannot_edit_or_delete_user_as_event(
    client: AsyncClient,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-17, NFR-6, rule T7: `EventNotFound`, and nothing of A's changes."""
    user_a, user_b = two_users
    event = await _create_event(session_factory, user_id=user_a)
    headers_b = _headers(signing_key, settings, user_id=user_b)

    edited = await _graphql(
        client,
        query=UPDATE,
        headers=headers_b,
        id=str(event.id),
        input=_input(days_ahead=12, title="Taken"),
    )
    deleted = await _graphql(client, query=DELETE, headers=headers_b, id=str(event.id))
    not_an_id = await _graphql(client, query=DELETE, headers=headers_b, id="abc")

    assert edited["updateEvent"]["__typename"] == "EventNotFound"
    assert deleted["deleteEvent"]["__typename"] == "EventNotFound"
    assert not_an_id["deleteEvent"]["__typename"] == "EventNotFound"
    assert (
        len(await _live_alerts(session_factory, user_id=user_a, event_id=event.id)) == 1
    )
