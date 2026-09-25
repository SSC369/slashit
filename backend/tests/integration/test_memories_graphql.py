"""Memories end to end against a real database: schema, auth, resolver, deps,
interactor, repository, pgvector, full-text search and RLS.

Sub-plan 4.1 cases C-1, C-8, C-9, C-10, C-12, C-14 and C-16. The model is the
one thing faked: ``LangChainGeminiProvider`` is patched at the class, so every
layer above it, the gateway's usage rows included, runs for real.
"""

import statistics
import time
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql import text

from app.core import auth as auth_module
from app.core.db import user_transaction
from app.core.settings import Settings
from app.domains.gateway.interfaces.dtos import (
    ExtractionRequest,
    ProviderEmbedding,
    ProviderResult,
)
from app.domains.gateway.services.langchain_provider import LangChainGeminiProvider

ALGORITHM = "ES256"

SUBMIT = """
mutation($rawInput: String!) {
  submitCapture(rawInput: $rawInput) {
    __typename
    ... on MemorySaved { memory { id text category origin } secretCaution }
    ... on MemoriesListed { memories { id text } searchText }
    ... on MemoryTooLong { length limit }
  }
}
"""


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


@pytest.fixture
def fake_model(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Categorises by a keyword and embeds to a fixed vector. Returns the
    prompts the judgement call received, so a test can assert what the model
    was shown."""
    prompts: list[str] = []

    async def generate(
        self: LangChainGeminiProvider, request: ExtractionRequest
    ) -> ProviderResult:
        prompts.append(request.prompt)
        category = "life" if "passport" in request.prompt.lower() else "people"
        return ProviderResult(
            data={"category": category, "conflicting_ids": []},
            input_tokens=120,
            output_tokens=12,
            model="fake-flash",
        )

    async def embed(self: LangChainGeminiProvider, *, text: str) -> ProviderEmbedding:
        return ProviderEmbedding(vector=tuple([0.01] * 768), model="fake-embed")

    monkeypatch.setattr(LangChainGeminiProvider, "generate", generate)
    monkeypatch.setattr(LangChainGeminiProvider, "embed", embed)
    return prompts


def _headers(
    key: ec.EllipticCurvePrivateKey, settings: Settings, *, user_id: uuid.UUID
) -> dict[str, str]:
    claims: dict[str, Any] = {
        "sub": str(user_id),
        "iss": settings.jwt_issuer,
        "exp": datetime.now(UTC) + timedelta(hours=1),
    }
    return {"Authorization": f"Bearer {jwt.encode(claims, key, algorithm=ALGORITHM)}"}


async def _graphql(
    client: AsyncClient,
    headers: dict[str, str],
    query: str,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response = await client.post(
        "/graphql", json={"query": query, "variables": variables or {}}, headers=headers
    )
    body: dict[str, Any] = response.json()
    assert "errors" not in body, body
    data: dict[str, Any] = body["data"]
    return data


async def _submit(
    client: AsyncClient, headers: dict[str, str], raw_input: str
) -> dict[str, Any]:
    data = await _graphql(client, headers, SUBMIT, {"rawInput": raw_input})
    result: dict[str, Any] = data["submitCapture"]
    return result


@pytest.mark.usefixtures("patched_jwks", "fake_model")
async def test_remember_saves_a_categorised_memory_with_a_vector(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """C-1 end to end, with the gateway's usage rows (C-11) in the database."""
    user_a, _ = two_users
    headers = _headers(signing_key, settings, user_id=user_a)

    result = await _submit(client, headers, "/remember My passport expires in 2030")

    assert result["__typename"] == "MemorySaved"
    assert result["memory"]["text"] == "My passport expires in 2030"
    assert result["memory"]["category"] == "LIFE"
    assert result["secretCaution"] is None
    async with session_factory() as session, user_transaction(session, user_a) as s:
        has_vector = await s.scalar(
            text("SELECT embedding IS NOT NULL FROM memories WHERE id = :id"),
            {"id": result["memory"]["id"]},
        )
        operations = (
            await s.execute(
                text("SELECT operation FROM ai_usage WHERE user_id = :u ORDER BY 1"),
                {"u": user_a},
            )
        ).scalars()
        assert has_vector is True
        assert list(operations) == ["generate", "embed"]


@pytest.mark.usefixtures("patched_jwks", "fake_model")
async def test_lookup_uses_real_full_text_search(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-8 against PostgreSQL: stop words dropped, stems matched."""
    user_a, _ = two_users
    headers = _headers(signing_key, settings, user_id=user_a)
    await _submit(client, headers, "/remember Career goal: backend engineer by 2027")
    await _submit(client, headers, "/remember Mom's birthday is October 12")

    found = await _submit(
        client, headers, "/memories what do you remember about my careers?"
    )
    nothing = await _submit(client, headers, "/memories visa")

    assert found["__typename"] == "MemoriesListed"
    assert [memory["text"] for memory in found["memories"]] == [
        "Career goal: backend engineer by 2027"
    ]
    assert found["searchText"] == "what do you remember about my careers?"
    assert nothing["memories"] == []


@pytest.mark.usefixtures("patched_jwks", "fake_model")
async def test_an_over_long_fact_is_refused_with_its_length(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    user_a, _ = two_users
    headers = _headers(signing_key, settings, user_id=user_a)

    result = await _submit(client, headers, "/remember " + "x" * 612)

    assert result == {"__typename": "MemoryTooLong", "length": 612, "limit": 500}


@pytest.mark.usefixtures("patched_jwks", "fake_model", "job_queue")
async def test_tab_detail_edit_and_all_records(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """C-9, C-10 and C-16 through GraphQL."""
    user_a, _ = two_users
    headers = _headers(signing_key, settings, user_id=user_a)
    saved = await _submit(client, headers, "/remember My passport expires in 2030")
    await _submit(client, headers, "/remember Dad prefers aisle seats")
    memory_id = saved["memory"]["id"]

    # One root field per request: fields in one request share its database
    # session, and resolve concurrently (dev log, note N-1).
    tab = await _graphql(
        client, headers, "{ memories(filter: {category: LIFE}) { text } }"
    )
    tab |= await _graphql(client, headers, "{ all: memories { text } }")
    tab |= await _graphql(
        client, headers, "{ records { __typename ... on Memory { text } } }"
    )
    edited = await _graphql(
        client,
        headers,
        "mutation($id: ID!) { updateMemory(id: $id, input: "
        '{text: "My passport expires in March 2030", category: LIFE}) '
        "{ __typename ... on Memory { text category origin } } }",
        {"id": memory_id},
    )
    too_long = await _graphql(
        client,
        headers,
        "mutation($id: ID!, $t: String!) { updateMemory(id: $id, input: "
        "{text: $t, category: null}) { __typename ... on MemoryTooLong { length } } }",
        {"id": memory_id, "t": "y" * 501},
    )

    assert [memory["text"] for memory in tab["memories"]] == [
        "My passport expires in 2030"
    ]
    assert len(tab["all"]) == 2
    assert {item["__typename"] for item in tab["records"]} == {"Memory"}
    assert edited["updateMemory"] == {
        "__typename": "Memory",
        "text": "My passport expires in March 2030",
        "category": "LIFE",
        "origin": "edit",
    }
    assert too_long["updateMemory"] == {"__typename": "MemoryTooLong", "length": 501}
    async with session_factory() as session, user_transaction(session, user_a) as s:
        vector_cleared = await s.scalar(
            text("SELECT embedding IS NULL FROM memories WHERE id = :id"),
            {"id": memory_id},
        )
    assert vector_cleared is True


@pytest.mark.usefixtures("patched_jwks", "fake_model", "job_queue")
async def test_user_b_never_sees_or_edits_user_a_memories(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-12, NFR-1, rule T7."""
    user_a, user_b = two_users
    saved = await _submit(
        client,
        _headers(signing_key, settings, user_id=user_a),
        "/remember My passport expires in 2030",
    )
    headers_b = _headers(signing_key, settings, user_id=user_b)

    seen = await _graphql(client, headers_b, "{ memories { id } }")
    seen |= await _graphql(client, headers_b, "{ records { __typename } }")
    seen |= await _graphql(
        client,
        headers_b,
        "query($id: ID!) { memory(id: $id) { __typename } }",
        {"id": saved["memory"]["id"]},
    )
    edit = await _graphql(
        client,
        headers_b,
        "mutation($id: ID!) { updateMemory(id: $id, input: "
        '{text: "stolen", category: null}) { __typename } }',
        {"id": saved["memory"]["id"]},
    )
    lookup = await _submit(client, headers_b, "/memories passport")

    assert seen["memories"] == []
    assert seen["records"] == []
    assert seen["memory"] == {"__typename": "MemoryNotFound"}
    assert edit["updateMemory"] == {"__typename": "MemoryNotFound"}
    assert lookup["memories"] == []


async def test_a_forgotten_row_cannot_keep_its_text(
    two_users: tuple[uuid.UUID, uuid.UUID],
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """AD-2: the tombstone rule holds in the database, before slice 3 exists."""
    user_a, _ = two_users
    memory_id = uuid.uuid4()
    async with session_factory() as session, user_transaction(session, user_a) as s:
        await s.execute(
            text(
                "INSERT INTO memories (id, user_id, text, origin, created_at, "
                "updated_at) VALUES (:id, :u, 'secret', 'command', now(), now())"
            ),
            {"id": memory_id, "u": user_a},
        )
    with pytest.raises(IntegrityError):
        async with (
            session_factory() as session,
            user_transaction(session, user_a) as s,
        ):
            await s.execute(
                text("UPDATE memories SET deleted_at = now() WHERE id = :id"),
                {"id": memory_id},
            )


@pytest.mark.usefixtures("patched_jwks")
async def test_lists_and_lookup_stay_fast_at_a_thousand_memories(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """C-14, NFR-5: under 1 s at p95 with 1,000 memories. Measured locally,
    in-process; a hosted database adds network time this cannot see."""
    user_a, _ = two_users
    async with session_factory() as session, user_transaction(session, user_a) as s:
        await s.execute(
            text(
                "INSERT INTO memories (id, user_id, text, category, origin, "
                "created_at, updated_at) SELECT gen_random_uuid(), :u, "
                "'Fact number ' || n || ' about travel and family plans', "
                "'life', 'command', now(), now() FROM generate_series(1, 1000) n"
            ),
            {"u": user_a},
        )
    headers = _headers(signing_key, settings, user_id=user_a)
    timings: list[float] = []
    for _ in range(20):
        started = time.perf_counter()
        await _graphql(client, headers, "{ memories { id text category } }")
        await _submit(client, headers, "/memories family travel")
        timings.append((time.perf_counter() - started) / 2)

    p95 = statistics.quantiles(timings, n=20)[-1]
    print(f"NFR-5 local p95 per call: {p95 * 1000:.0f} ms")
    assert p95 < 1.0
