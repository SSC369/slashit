"""Settings and profile end to end: schema, auth, resolver, interactor,
repository, RLS."""

import json
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
    key: ec.EllipticCurvePrivateKey,
    settings: Settings,
    *,
    user_id: uuid.UUID,
    email: str | None = None,
) -> str:
    claims: dict[str, Any] = {
        "sub": str(user_id),
        "iss": settings.jwt_issuer,
        "exp": datetime.now(UTC) + timedelta(hours=1),
    }
    if email is not None:
        claims["email"] = email
    return jwt.encode(claims, key, algorithm=ALGORITHM)


async def test_settings_creates_a_row_with_the_detected_timezone(
    client: AsyncClient,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """T-2.10."""
    user_a, _user_b = two_users
    token = _token(signing_key, settings, user_id=user_a)

    response = await client.post(
        "/graphql",
        json={
            "query": (
                "query($tz: String) { settings(detectedTimezone: $tz) { timezone } }"
            ),
            "variables": {"tz": "Asia/Kolkata"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    body = response.json()

    assert response.status_code == 200, body
    assert body["data"]["settings"] == {"timezone": "Asia/Kolkata"}


async def test_settings_second_call_returns_the_same_row(
    client: AsyncClient,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """T-2.10."""
    user_a, _user_b = two_users
    token = _token(signing_key, settings, user_id=user_a)
    headers = {"Authorization": f"Bearer {token}"}
    query = "query($tz: String) { settings(detectedTimezone: $tz) { timezone } }"

    first = await client.post(
        "/graphql",
        json={"query": query, "variables": {"tz": "Asia/Kolkata"}},
        headers=headers,
    )
    second = await client.post(
        "/graphql",
        json={"query": query, "variables": {"tz": "America/New_York"}},
        headers=headers,
    )

    assert first.json()["data"]["settings"]["timezone"] == "Asia/Kolkata"
    assert second.json()["data"]["settings"]["timezone"] == "Asia/Kolkata"


async def test_update_timezone_changes_the_value(
    client: AsyncClient,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    two_users: tuple[uuid.UUID, uuid.UUID],
    job_queue: None,
) -> None:
    user_a, _user_b = two_users
    token = _token(signing_key, settings, user_id=user_a)

    response = await client.post(
        "/graphql",
        json={
            "query": (
                "mutation($input: UpdateTimezoneInput!) "
                "{ updateTimezone(input: $input) "
                "{ __typename ... on Settings { timezone } } }"
            ),
            "variables": {"input": {"timezone": "Europe/London"}},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    body = response.json()

    assert body["data"]["updateTimezone"] == {
        "__typename": "Settings",
        "timezone": "Europe/London",
    }


async def test_update_timezone_with_an_invalid_zone_is_refused(
    client: AsyncClient,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """T-2.12."""
    user_a, _user_b = two_users
    token = _token(signing_key, settings, user_id=user_a)

    response = await client.post(
        "/graphql",
        json={
            "query": (
                "mutation($input: UpdateTimezoneInput!) "
                "{ updateTimezone(input: $input) { __typename } }"
            ),
            "variables": {"input": {"timezone": "not/a/zone"}},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    body = response.json()

    assert body["data"]["updateTimezone"]["__typename"] == "InvalidTimezone"


async def test_user_a_and_user_b_each_get_their_own_settings_row(
    client: AsyncClient,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """T-2.13, rule T7."""
    user_a, user_b = two_users
    query = "query($tz: String) { settings(detectedTimezone: $tz) { timezone } }"

    token_a = _token(signing_key, settings, user_id=user_a)
    await client.post(
        "/graphql",
        json={"query": query, "variables": {"tz": "Asia/Kolkata"}},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    token_b = _token(signing_key, settings, user_id=user_b)
    response_b = await client.post(
        "/graphql",
        json={"query": query, "variables": {"tz": "Pacific/Auckland"}},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert response_b.json()["data"]["settings"] == {"timezone": "Pacific/Auckland"}


async def test_me_generates_a_username_when_signup_metadata_carried_none(
    client: AsyncClient,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """Was T-1.5's "`me` returns `username: null`" case under migration 0007.
    Migration 0010 (04.3-google-sign-in, the Google-signup fallback) changed
    `handle_new_user()` so any signup with no `username` in
    `raw_user_meta_data` — Google's path, and this fixture's — gets a
    generated `user_<id prefix>` instead of a null column. `two_users`
    inserts `auth.users` rows with no `raw_user_meta_data`, so this now
    exercises the fallback rather than a null username."""
    user_a, _user_b = two_users
    email = f"{user_a}@rls-test.invalid"  # matches conftest's two_users fixture
    token = _token(signing_key, settings, user_id=user_a, email=email)

    response = await client.post(
        "/graphql",
        json={"query": "{ me { id email username } }"},
        headers={"Authorization": f"Bearer {token}"},
    )
    body = response.json()

    assert response.status_code == 200, body
    assert body["data"]["me"]["id"] == str(user_a)
    assert body["data"]["me"]["email"] == email
    assert body["data"]["me"]["username"] == f"user_{str(user_a)[:8]}"


async def test_me_returns_the_username_the_trigger_stored_at_signup(
    client: AsyncClient,
    signing_key: ec.EllipticCurvePrivateKey,
    patched_jwks: None,
    settings: Settings,
    engine: AsyncEngine,
) -> None:
    """T-1.5: the username `handle_new_user()` copied from
    `raw_user_meta_data` at signup comes back on `me`, proving the resolver
    reads the trigger's row rather than anything computed here."""
    user_id = uuid.uuid4()
    email = f"{user_id}@rls-test.invalid"
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO auth.users "
                "(id, email, instance_id, raw_user_meta_data) "
                "VALUES (:id, :email, "
                "'00000000-0000-0000-0000-000000000000', :meta)"
            ),
            {"id": user_id, "email": email, "meta": json.dumps({"username": "sai"})},
        )
    try:
        token = _token(signing_key, settings, user_id=user_id, email=email)

        response = await client.post(
            "/graphql",
            json={"query": "{ me { id email username } }"},
            headers={"Authorization": f"Bearer {token}"},
        )
        body = response.json()

        assert response.status_code == 200, body
        assert body["data"]["me"] == {
            "id": str(user_id),
            "email": email,
            "username": "sai",
        }
    finally:
        async with engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM auth.users WHERE id = :id"), {"id": user_id}
            )
