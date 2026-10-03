"""Events end to end: schema, auth, resolver, deps, interactor, repository,
RLS. Epic 007, sub-plan 4.1 §7, and rule T7's boundary case.

Events are created through the real repository, since creating one through
`/add-event` needs the model; the capture path is covered in unit tests.
"""

import asyncio
import uuid
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import auth as auth_module
from app.core.settings import Settings
from app.domains.events.interfaces.dtos import EventWrite, StoredEventDTO
from app.domains.events.repositories.calendar_event_repository import (
    SqlCalendarEventRepository,
)
from app.domains.events.services.schedule import LocalSchedule, resolve

ALGORITHM = "ES256"
ZONE = "Asia/Kolkata"


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


async def _create(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    user_id: uuid.UUID,
    title: str,
    start_date: date,
    start_time: time | None = None,
    limit: int = 500,
) -> StoredEventDTO | None:
    now = datetime.now(UTC)
    schedule = LocalSchedule(
        start_date=start_date,
        start_time=start_time,
        end_date=None,
        end_time=None,
        repeat_yearly=False,
        timezone=ZONE,
    )
    resolved = resolve(schedule=schedule, now=now)
    async with session_factory() as session:
        return await SqlCalendarEventRepository(session).create_event_if_upcoming_below(
            user_id=user_id,
            write=EventWrite(
                title=title,
                location=None,
                description=None,
                schedule=schedule,
                starts_at=resolved.starts_at,
                ends_at=resolved.ends_at,
                alert_leads_minutes=(),
                origin="command",
                original_input=f"/add-event {title}",
            ),
            limit=limit,
            now=now,
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
    data: dict[str, Any] = body["data"]
    return data


EVENTS_QUERY = """
query Events($scope: EventScope!) {
  events(scope: $scope) { id title status whenText occurrenceDate allDay }
}
"""

EVENT_QUERY = """
query Event($id: ID!) {
  event(id: $id) {
    __typename
    ... on Event { id title status }
    ... on EventNotFound { message }
  }
}
"""

RECORDS_QUERY = """
query { records(filter: {kind: "ALL"}) { __typename ... on Event { id title } } }
"""


async def test_events_lists_upcoming_and_all_adds_past(
    client: AsyncClient,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """FR-24, FR-25, FR-26."""
    user_a, _ = two_users
    today = datetime.now(UTC).date()
    later = await _create(
        session_factory, user_id=user_a, title="Later", start_date=today + timedelta(9)
    )
    sooner = await _create(
        session_factory, user_id=user_a, title="Sooner", start_date=today + timedelta(2)
    )
    past = await _create(
        session_factory, user_id=user_a, title="Past", start_date=date(2019, 6, 14)
    )
    assert later and sooner and past
    headers = _headers(signing_key, settings, user_id=user_a)

    upcoming = await _graphql(
        client, query=EVENTS_QUERY, headers=headers, scope="UPCOMING"
    )
    assert [item["title"] for item in upcoming["events"]] == ["Sooner", "Later"]
    assert upcoming["events"][0]["allDay"] is True

    every = await _graphql(client, query=EVENTS_QUERY, headers=headers, scope="ALL")
    assert [item["title"] for item in every["events"]] == ["Sooner", "Later", "Past"]
    assert every["events"][2]["status"] == "PAST"

    records = await _graphql(client, query=RECORDS_QUERY, headers=headers)
    event_titles = {
        item["title"] for item in records["records"] if item["__typename"] == "Event"
    }
    assert event_titles == {"Sooner", "Later", "Past"}


async def test_another_users_event_is_not_found_anywhere(
    client: AsyncClient,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """NFR-6, rule T7: B reading A's event by id, list or All gets nothing."""
    user_a, user_b = two_users
    event = await _create(
        session_factory,
        user_id=user_a,
        title="Private",
        start_date=datetime.now(UTC).date() + timedelta(3),
    )
    assert event is not None
    headers_b = _headers(signing_key, settings, user_id=user_b)

    detail = await _graphql(
        client, query=EVENT_QUERY, headers=headers_b, id=str(event.id)
    )
    assert detail["event"]["__typename"] == "EventNotFound"
    listed = await _graphql(client, query=EVENTS_QUERY, headers=headers_b, scope="ALL")
    assert listed["events"] == []
    records = await _graphql(client, query=RECORDS_QUERY, headers=headers_b)
    assert all(item["__typename"] != "Event" for item in records["records"])

    own = await _graphql(
        client,
        query=EVENT_QUERY,
        headers=_headers(signing_key, settings, user_id=user_a),
        id=str(event.id),
    )
    assert own["event"]["title"] == "Private"


async def test_concurrent_creates_at_the_cap_give_exactly_one_success(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """FR-31's race: the per-user advisory lock lets one of two creates at
    ``limit - 1`` through. A limit of 2 stands in for 500."""
    user_a, _ = two_users
    start = datetime.now(UTC).date() + timedelta(5)
    assert await _create(
        session_factory, user_id=user_a, title="First", start_date=start, limit=2
    )
    outcomes = await asyncio.gather(
        *(
            _create(
                session_factory, user_id=user_a, title=title, start_date=start, limit=2
            )
            for title in ("Second", "Third")
        )
    )
    assert sum(outcome is not None for outcome in outcomes) == 1
