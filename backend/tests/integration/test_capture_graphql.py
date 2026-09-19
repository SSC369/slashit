"""submitCapture end to end: schema, auth, resolver, deps, interactor,
repository, RLS. The paths exercised here call no vendor and cost nothing;
the real-extraction path is test_capture_live.py, marked ``live``.
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


async def test_tasks_command_lists_open_tasks(
    client: AsyncClient,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """/tasks calls no vendor, so this proves the whole wire end to end
    without spending anything: schema to resolver to interactor to
    repository to RLS and back."""
    user_a, _user_b = two_users
    token = _token(signing_key, settings, user_id=user_a)

    response = await client.post(
        "/graphql",
        json={
            "query": (
                "mutation($input: String!) { submitCapture(rawInput: $input) "
                "{ __typename ... on TasksListed { tasks { title } } } }"
            ),
            "variables": {"input": "/tasks"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    body = response.json()

    assert response.status_code == 200, body
    assert body["data"]["submitCapture"]["__typename"] == "TasksListed"
    assert body["data"]["submitCapture"]["tasks"] == []


async def test_non_command_input_returns_guidance_end_to_end(
    client: AsyncClient,
    engine: AsyncEngine,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """FR-9, also calls no vendor. Also writes the PRD section 8 metric event
    for a session where the user typed without a command."""
    user_a, _user_b = two_users
    token = _token(signing_key, settings, user_id=user_a)

    response = await client.post(
        "/graphql",
        json={
            "query": (
                "mutation($input: String!) { submitCapture(rawInput: $input) "
                "{ __typename ... on NonCommandGuidance { originalInput } } }"
            ),
            "variables": {"input": "buy milk tomorrow"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    body = response.json()

    assert response.status_code == 200, body
    assert body["data"]["submitCapture"]["__typename"] == "NonCommandGuidance"
    assert body["data"]["submitCapture"]["originalInput"] == "buy milk tomorrow"

    async with engine.begin() as conn:
        event_type = await conn.scalar(
            text("SELECT event_type FROM events WHERE user_id = :user_id"),
            {"user_id": user_a},
        )
    assert event_type == "no_command_input"


async def test_submit_capture_refuses_without_a_token(client: AsyncClient) -> None:
    """IsAuthenticated closes this the same as every other protected field."""
    response = await client.post(
        "/graphql",
        json={
            "query": ('mutation { submitCapture(rawInput: "/tasks") { __typename } }')
        },
    )
    body = response.json()

    assert body.get("errors")
    assert "Not authenticated" in str(body["errors"])
