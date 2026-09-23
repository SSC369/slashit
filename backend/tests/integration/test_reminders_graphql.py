"""Reminders end to end: schema, auth, resolver, deps, interactor, repository,
RLS. TC-1.19 to TC-1.21 of sub-plan 4.1, and rule T7's boundary case.

Rows are seeded straight into the table as the owning user, since creating one
through `/remind` needs the model; the create path is covered in unit tests.
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
from app.core.db import user_transaction
from app.core.settings import Settings

ALGORITHM = "ES256"

INSERT_REMINDER = text(
    "INSERT INTO reminders (id, user_id, description, repeat_kind, repeat_interval, "
    "repeat_weekdays, local_time, anchor_local_date, one_time_at, next_fire_at, "
    "schedule_timezone, state, origin, created_at, updated_at) VALUES "
    "(:id, :user_id, :description, 'none', 1, '{}', :local_time, :anchor, "
    ":fire_at, :fire_at, 'Asia/Kolkata', :state, 'command', now(), now())"
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


async def _seed(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    user_id: uuid.UUID,
    description: str,
    days_ahead: int,
    state: str = "upcoming",
) -> uuid.UUID:
    reminder_id = uuid.uuid4()
    fire_at = datetime.now(UTC).replace(second=0, microsecond=0) + timedelta(
        days=days_ahead
    )
    async with session_factory() as session, user_transaction(session, user_id) as s:
        await s.execute(
            INSERT_REMINDER,
            {
                "id": reminder_id,
                "user_id": user_id,
                "description": description,
                "local_time": time(19),
                "anchor": fire_at.date(),
                "fire_at": fire_at,
                "state": state,
            },
        )
    return reminder_id


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


REMINDERS_QUERY = """
query($search: String) {
  reminders(search: $search) {
    needsAttention { id description }
    upcoming { id description whenText repeatText }
    done { id }
  }
}
"""


async def test_reminders_groups_and_orders_the_tab(
    client: AsyncClient,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """TC-1.19, FR-26."""
    user_a, _ = two_users
    later = await _seed(
        session_factory, user_id=user_a, description="Later", days_ahead=5
    )
    sooner = await _seed(
        session_factory, user_id=user_a, description="Sooner", days_ahead=1
    )
    fired = await _seed(
        session_factory,
        user_id=user_a,
        description="Fired",
        days_ahead=-1,
        state="fired",
    )

    data = await _graphql(
        client,
        query=REMINDERS_QUERY,
        headers=_headers(signing_key, settings, user_id=user_a),
    )

    groups = data["reminders"]
    assert [item["id"] for item in groups["upcoming"]] == [str(sooner), str(later)]
    assert [item["id"] for item in groups["needsAttention"]] == [str(fired)]
    assert groups["upcoming"][0]["repeatText"] == "Does not repeat"


async def test_another_users_reminder_is_not_found_for_every_operation(
    client: AsyncClient,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """TC-1.20, NFR-6, rule T7: B reading, editing or deleting A's reminder
    gets the same answer as a missing id, and A's row is unchanged."""
    user_a, user_b = two_users
    reminder_id = await _seed(
        session_factory, user_id=user_a, description="A's reminder", days_ahead=2
    )
    b_headers = _headers(signing_key, settings, user_id=user_b)

    read = await _graphql(
        client,
        query="query($id: ID!) { reminder(id: $id) { __typename } }",
        headers=b_headers,
        id=str(reminder_id),
    )
    edited = await _graphql(
        client,
        query=(
            "mutation($id: ID!, $input: UpdateReminderInput!) { updateReminder("
            "id: $id, input: $input) { __typename } }"
        ),
        headers=b_headers,
        id=str(reminder_id),
        input={
            "description": "stolen",
            "startDate": (date.today() + timedelta(days=3)).isoformat(),
            "localTime": "09:00",
            "repeatKind": "NONE",
        },
    )
    deleted = await _graphql(
        client,
        query="mutation($id: ID!) { deleteReminder(id: $id) { __typename } }",
        headers=b_headers,
        id=str(reminder_id),
    )
    b_list = await _graphql(client, query=REMINDERS_QUERY, headers=b_headers)

    assert read["reminder"]["__typename"] == "ReminderNotFound"
    assert edited["updateReminder"]["__typename"] == "ReminderNotFound"
    assert deleted["deleteReminder"]["__typename"] == "ReminderNotFound"
    assert b_list["reminders"]["upcoming"] == []
    owner_view = await _graphql(
        client,
        query=(
            "query($id: ID!) { reminder(id: $id) { ... on Reminder { description } } }"
        ),
        headers=_headers(signing_key, settings, user_id=user_a),
        id=str(reminder_id),
    )
    assert owner_view["reminder"]["description"] == "A's reminder"


async def test_edit_then_delete_through_the_api(
    client: AsyncClient,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """FR-28 to FR-30 over the wire, including the field error union member."""
    user_a, _ = two_users
    headers = _headers(signing_key, settings, user_id=user_a)
    reminder_id = await _seed(
        session_factory, user_id=user_a, description="Standup", days_ahead=1
    )
    update_mutation = (
        "mutation($id: ID!, $input: UpdateReminderInput!) { updateReminder(id: $id, "
        "input: $input) { __typename ... on Reminder { repeatText } "
        "... on InvalidReminder { field } } }"
    )
    next_monday = date.today() + timedelta(days=(7 - date.today().weekday()) or 7)

    invalid = await _graphql(
        client,
        query=update_mutation,
        headers=headers,
        id=str(reminder_id),
        input={
            "description": "Standup",
            "startDate": next_monday.isoformat(),
            "localTime": "09:30",
            "repeatKind": "WEEKLY",
            "repeatWeekdays": [],
        },
    )
    updated = await _graphql(
        client,
        query=update_mutation,
        headers=headers,
        id=str(reminder_id),
        input={
            "description": "Standup",
            "startDate": next_monday.isoformat(),
            "localTime": "09:30",
            "repeatKind": "WEEKLY",
            "repeatWeekdays": [0, 1, 2, 3, 4],
        },
    )
    deleted = await _graphql(
        client,
        query="mutation($id: ID!) { deleteReminder(id: $id) { __typename } }",
        headers=headers,
        id=str(reminder_id),
    )
    after = await _graphql(
        client,
        query="query($id: ID!) { reminder(id: $id) { __typename } }",
        headers=headers,
        id=str(reminder_id),
    )

    assert invalid["updateReminder"] == {
        "__typename": "InvalidReminder",
        "field": "repeatWeekdays",
    }
    assert updated["updateReminder"]["repeatText"] == "Every weekday"
    assert deleted["deleteReminder"]["__typename"] == "ReminderDeleteSucceeded"
    assert after["reminder"]["__typename"] == "ReminderNotFound"


async def test_the_all_tab_lists_reminders_beside_tasks(
    client: AsyncClient,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """FR-26: reminders appear under All; the Tasks filter still excludes them."""
    user_a, _ = two_users
    headers = _headers(signing_key, settings, user_id=user_a)
    await _seed(session_factory, user_id=user_a, description="Call Mom", days_ahead=1)
    records_query = (
        "query($filter: RecordsFilterInput) { records(filter: $filter) "
        "{ __typename ... on Reminder { description } } }"
    )

    everything = await _graphql(client, query=records_query, headers=headers)
    tasks_only = await _graphql(
        client, query=records_query, headers=headers, filter={"kind": "TASKS"}
    )

    assert {"__typename": "Reminder", "description": "Call Mom"} in everything[
        "records"
    ]
    assert all(item["__typename"] == "Task" for item in tasks_only["records"])
