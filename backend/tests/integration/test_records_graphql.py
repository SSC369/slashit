"""Records end to end: schema, auth, resolver, interactor, repository, RLS.

No vendor call anywhere in this file: every task here is seeded by a direct
insert, not through capture, so this costs nothing and runs unconditionally.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.sql import text

from app.core import auth as auth_module
from app.core.settings import Settings

ALGORITHM = "ES256"

INSERT_TASK = text(
    "INSERT INTO tasks "
    "(id, user_id, title, due_at, status, origin, original_input, "
    "created_at, updated_at) "
    "VALUES (:id, :user_id, :title, :due_at, 'pending', 'command', :original_input, "
    "now(), now())"
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


def _token(
    key: ec.EllipticCurvePrivateKey, settings: Settings, *, user_id: uuid.UUID
) -> str:
    claims: dict[str, Any] = {
        "sub": str(user_id),
        "iss": settings.jwt_issuer,
        "exp": datetime.now(UTC) + timedelta(hours=1),
    }
    return jwt.encode(claims, key, algorithm=ALGORITHM)


async def _insert_task(
    engine: AsyncEngine,
    *,
    user_id: uuid.UUID,
    title: str = "Finish API docs",
    due_at: datetime | None = None,
) -> uuid.UUID:
    task_id = uuid.uuid4()
    async with engine.begin() as conn:
        # A superuser connection bypasses RLS (rule T3), which is fine for
        # seeding: the assertions below are what actually exercise the policy.
        await conn.execute(
            INSERT_TASK,
            {
                "id": task_id,
                "user_id": user_id,
                "title": title,
                "due_at": due_at,
                "original_input": f"/add-task {title}",
            },
        )
    return task_id


async def test_records_query_lists_a_seeded_task(
    client: AsyncClient,
    engine: AsyncEngine,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    user_a, _user_b = two_users
    await _insert_task(engine, user_id=user_a)
    token = _token(signing_key, settings, user_id=user_a)

    response = await client.post(
        "/graphql",
        json={"query": "query { records { ... on Task { title } } }"},
        headers={"Authorization": f"Bearer {token}"},
    )
    body = response.json()

    assert response.status_code == 200, body
    assert body["data"]["records"] == [{"title": "Finish API docs"}]


async def test_record_by_id_returns_full_detail(
    client: AsyncClient,
    engine: AsyncEngine,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """FR-18, FR-22."""
    user_a, _user_b = two_users
    task_id = await _insert_task(engine, user_id=user_a)
    token = _token(signing_key, settings, user_id=user_a)

    response = await client.post(
        "/graphql",
        json={
            "query": (
                "query($id: ID!) { record(id: $id) "
                "{ __typename ... on Task { title origin originalInput } } }"
            ),
            "variables": {"id": str(task_id)},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    body = response.json()

    assert response.status_code == 200, body
    assert body["data"]["record"] == {
        "__typename": "Task",
        "title": "Finish API docs",
        "origin": "command",
        "originalInput": "/add-task Finish API docs",
    }


async def test_record_returns_not_found_for_a_missing_id(
    client: AsyncClient,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    user_a, _user_b = two_users
    token = _token(signing_key, settings, user_id=user_a)

    response = await client.post(
        "/graphql",
        json={
            "query": "query($id: ID!) { record(id: $id) { __typename } }",
            "variables": {"id": str(uuid.uuid4())},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    body = response.json()

    assert body["data"]["record"]["__typename"] == "RecordNotFound"


async def test_update_task_changes_the_title(
    client: AsyncClient,
    engine: AsyncEngine,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """FR-19."""
    user_a, _user_b = two_users
    task_id = await _insert_task(engine, user_id=user_a)
    token = _token(signing_key, settings, user_id=user_a)

    response = await client.post(
        "/graphql",
        json={
            "query": (
                "mutation($id: ID!, $input: UpdateTaskInput!) "
                "{ updateTask(id: $id, input: $input) "
                "{ __typename ... on Task { title } } }"
            ),
            "variables": {"id": str(task_id), "input": {"title": "Finish the docs"}},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    body = response.json()

    assert body["data"]["updateTask"] == {
        "__typename": "Task",
        "title": "Finish the docs",
    }


async def test_update_task_with_no_fields_returns_no_fields_to_update(
    client: AsyncClient,
    engine: AsyncEngine,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    user_a, _user_b = two_users
    task_id = await _insert_task(engine, user_id=user_a)
    token = _token(signing_key, settings, user_id=user_a)

    response = await client.post(
        "/graphql",
        json={
            "query": (
                "mutation($id: ID!, $input: UpdateTaskInput!) "
                "{ updateTask(id: $id, input: $input) { __typename } }"
            ),
            "variables": {"id": str(task_id), "input": {}},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    body = response.json()

    assert body["data"]["updateTask"]["__typename"] == "NoFieldsToUpdate"


async def test_complete_task_sets_status_done(
    client: AsyncClient,
    engine: AsyncEngine,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    user_a, _user_b = two_users
    task_id = await _insert_task(engine, user_id=user_a)
    token = _token(signing_key, settings, user_id=user_a)

    response = await client.post(
        "/graphql",
        json={
            "query": (
                "mutation($id: ID!) { completeTask(id: $id) "
                "{ __typename ... on Task { status } } }"
            ),
            "variables": {"id": str(task_id)},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    body = response.json()

    assert body["data"]["completeTask"] == {"__typename": "Task", "status": "done"}


async def test_delete_task_soft_deletes_the_row(
    client: AsyncClient,
    engine: AsyncEngine,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """FR-20. User decision 2026-09-19: no task is ever hard-deleted, so the
    row survives with deleted_at set, and the records query no longer
    returns it."""
    user_a, _user_b = two_users
    task_id = await _insert_task(engine, user_id=user_a)
    token = _token(signing_key, settings, user_id=user_a)

    response = await client.post(
        "/graphql",
        json={
            "query": "mutation($ids: [ID!]!) { deleteTask(ids: $ids) }",
            "variables": {"ids": [str(task_id)]},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    body = response.json()

    assert body["data"]["deleteTask"] == 1

    async with engine.begin() as conn:
        deleted_at = await conn.scalar(
            text("SELECT deleted_at FROM tasks WHERE id = :id"), {"id": task_id}
        )
    assert deleted_at is not None, "the row should survive, marked deleted"

    records_response = await client.post(
        "/graphql",
        json={"query": "{ records { ... on Task { id } } }"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert records_response.json()["data"]["records"] == []


async def test_records_view_opened_writes_one_event(
    client: AsyncClient,
    engine: AsyncEngine,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """PRD section 8: weekly actives opening a records view."""
    user_a, _user_b = two_users
    token = _token(signing_key, settings, user_id=user_a)

    response = await client.post(
        "/graphql",
        json={"query": "mutation { recordsViewOpened }"},
        headers={"Authorization": f"Bearer {token}"},
    )
    body = response.json()

    assert body["data"]["recordsViewOpened"] is True

    async with engine.begin() as conn:
        event_type = await conn.scalar(
            text("SELECT event_type FROM events WHERE user_id = :user_id"),
            {"user_id": user_a},
        )
    assert event_type == "records_view_opened"


async def test_user_a_cannot_read_user_bs_record(
    client: AsyncClient,
    engine: AsyncEngine,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """T-2.9, rule T7."""
    user_a, user_b = two_users
    task_id = await _insert_task(engine, user_id=user_b, title="User B's task")
    token = _token(signing_key, settings, user_id=user_a)

    response = await client.post(
        "/graphql",
        json={
            "query": "query($id: ID!) { record(id: $id) { __typename } }",
            "variables": {"id": str(task_id)},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    body = response.json()

    assert body["data"]["record"]["__typename"] == "RecordNotFound"


async def test_user_a_cannot_update_user_bs_task(
    client: AsyncClient,
    engine: AsyncEngine,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """T-2.9, rule T7."""
    user_a, user_b = two_users
    task_id = await _insert_task(engine, user_id=user_b, title="User B's task")
    token = _token(signing_key, settings, user_id=user_a)

    response = await client.post(
        "/graphql",
        json={
            "query": (
                "mutation($id: ID!, $input: UpdateTaskInput!) "
                "{ updateTask(id: $id, input: $input) { __typename } }"
            ),
            "variables": {"id": str(task_id), "input": {"title": "Hijacked"}},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    body = response.json()

    assert body["data"]["updateTask"]["__typename"] == "RecordNotFound"


async def test_user_a_cannot_complete_user_bs_task(
    client: AsyncClient,
    engine: AsyncEngine,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """T-2.9, rule T7."""
    user_a, user_b = two_users
    task_id = await _insert_task(engine, user_id=user_b, title="User B's task")
    token = _token(signing_key, settings, user_id=user_a)

    response = await client.post(
        "/graphql",
        json={
            "query": "mutation($id: ID!) { completeTask(id: $id) { __typename } }",
            "variables": {"id": str(task_id)},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    body = response.json()

    assert body["data"]["completeTask"]["__typename"] == "RecordNotFound"


async def test_user_a_deleting_user_bs_task_deletes_nothing(
    client: AsyncClient,
    engine: AsyncEngine,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """T-2.9, rule T7."""
    user_a, user_b = two_users
    task_id = await _insert_task(engine, user_id=user_b, title="User B's task")
    token = _token(signing_key, settings, user_id=user_a)

    response = await client.post(
        "/graphql",
        json={
            "query": "mutation($ids: [ID!]!) { deleteTask(ids: $ids) }",
            "variables": {"ids": [str(task_id)]},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    body = response.json()

    assert body["data"]["deleteTask"] == 0

    async with engine.begin() as conn:
        remaining = await conn.scalar(
            text("SELECT count(*) FROM tasks WHERE id = :id"), {"id": task_id}
        )
    assert remaining == 1, "user A's failed delete should not have touched the row"
