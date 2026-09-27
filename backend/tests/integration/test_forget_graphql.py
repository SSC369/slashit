"""Forget end to end against a real database, sub-plan 4.2 cases C-2.1 to
C-2.3, C-2.9, C-2.10 and C-2.12, and sub-plan 4.5's C-5.1 and C-5.2.
NFR-2's search-every-table case is C-2.9.

The model is faked at ``LangChainGeminiProvider``, as in
``test_memories_graphql.py``, whose fixtures and helpers this reuses.
"""

import uuid

import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql import text

from app.core.settings import Settings, get_settings
from tests.integration.test_memories_graphql import (
    _graphql,
    _headers,
    _submit,
    fake_model,
    patched_jwks,
    signing_key,
)

__all__ = ["fake_model", "patched_jwks", "signing_key"]

HISTORY = """
{ captureHistory { items { inputText outcome forgotten affectedCount answerText } } }
"""

FACT = "My passport number is P7788123"


async def _text_found_anywhere(
    session_factory: async_sessionmaker[AsyncSession], needle: str
) -> list[str]:
    """Every text-like column of every table in `public`, searched as the
    superuser, so RLS cannot hide a leftover (NFR-2)."""
    hits: list[str] = []
    async with session_factory() as session, session.begin():
        columns = (
            await session.execute(
                text(
                    "SELECT table_name, column_name FROM information_schema.columns "
                    "WHERE table_schema = 'public' AND data_type IN "
                    "('text', 'character varying', 'jsonb', 'json', 'ARRAY')"
                )
            )
        ).all()
        for table_name, column_name in columns:
            found = await session.scalar(
                text(
                    f'SELECT count(*) FROM public."{table_name}" '
                    f'WHERE "{column_name}"::text ILIKE :needle'
                ),
                {"needle": f"%{needle}%"},
            )
            if found:
                hits.append(f"{table_name}.{column_name}")
    return hits


@pytest.mark.usefixtures("patched_jwks", "fake_model")
async def test_forget_from_records_leaves_no_trace(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """C-2.1, C-2.2, C-2.3 and C-2.9 (NFR-2)."""
    user_a, _ = two_users
    headers = _headers(signing_key, settings, user_id=user_a)
    # Saved once directly, once through FR-3's question and its answer.
    saved = await _submit(client, headers, f"/remember {FACT}")
    question = await _graphql(
        client,
        headers,
        'mutation { submitCapture(rawInput: "/remember") { __typename '
        "... on PendingQuestionCreated { pendingCaptureId } } }",
    )
    answered = await _graphql(
        client,
        headers,
        "mutation($id: ID!, $answer: String!) { answerPendingCapture("
        "pendingCaptureId: $id, answer: $answer) { __typename "
        "... on MemorySaved { memory { id } } } }",
        {
            "id": question["submitCapture"]["pendingCaptureId"],
            "answer": f"{FACT} again",
        },
    )
    first_id = saved["memory"]["id"]
    second_id = answered["answerPendingCapture"]["memory"]["id"]

    for memory_id in (first_id, second_id):
        forgotten = await _graphql(
            client,
            headers,
            "mutation($id: ID!) { forgetMemory(id: $id) { __typename "
            "... on MemoriesForgotten { count } } }",
            {"id": memory_id},
        )
        assert forgotten["forgetMemory"] == {
            "__typename": "MemoriesForgotten",
            "count": 1,
        }

    after = await _graphql(client, headers, "{ memories { id } }")
    lookup = await _submit(client, headers, "/memories passport")
    detail = await _graphql(
        client,
        headers,
        "query($id: ID!) { memory(id: $id) { __typename } }",
        {"id": first_id},
    )
    history = await _graphql(client, headers, HISTORY)

    assert after["memories"] == []
    assert lookup["memories"] == []
    assert detail["memory"] == {"__typename": "MemoryNotFound"}
    # Sub-plan 4.4: forget deletes the direct save, the answer and the
    # question it closed, and the memory rows, leaving no trace.
    items = history["captureHistory"]["items"]
    assert [item for item in items if item["forgotten"]] == []
    assert [
        item for item in items if item["outcome"] in {"MEMORY_SAVED", "QUESTION_ASKED"}
    ] == []
    async with session_factory() as session, session.begin():
        remaining = (
            await session.execute(
                text("SELECT count(*) FROM memories WHERE id IN (:first, :second)"),
                {"first": first_id, "second": second_id},
            )
        ).scalar_one()
    assert remaining == 0
    assert await _text_found_anywhere(session_factory, "P7788123") == []


@pytest.mark.usefixtures("patched_jwks", "fake_model")
async def test_user_b_cannot_forget_user_a_memories(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-2.10, NFR-1, T7."""
    user_a, user_b = two_users
    headers_a = _headers(signing_key, settings, user_id=user_a)
    headers_b = _headers(signing_key, settings, user_id=user_b)
    saved = await _submit(client, headers_a, "/remember Keep this one")
    memory_id = saved["memory"]["id"]

    from_records = await _graphql(
        client,
        headers_b,
        "mutation($id: ID!) { forgetMemory(id: $id) { __typename } }",
        {"id": memory_id},
    )
    still_there = await _graphql(client, headers_a, "{ memories { id } }")

    assert from_records["forgetMemory"] == {"__typename": "MemoryNotFound"}
    assert [memory["id"] for memory in still_there["memories"]] == [memory_id]


@pytest.mark.usefixtures("patched_jwks", "fake_model")
async def test_forget_works_with_the_gateway_switched_off(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """C-2.12: forget never calls the model."""
    user_a, _ = two_users
    headers = _headers(signing_key, settings, user_id=user_a)
    saved = await _submit(client, headers, "/remember Car insurance renews in March")
    monkeypatch.setattr(get_settings(), "gateway_enabled", False)

    confirmed = await _graphql(
        client,
        headers,
        "mutation($id: ID!) { forgetMemory(id: $id) { __typename "
        "... on MemoriesForgotten { count } } }",
        {"id": saved["memory"]["id"]},
    )

    assert confirmed["forgetMemory"] == {"__typename": "MemoriesForgotten", "count": 1}


@pytest.mark.usefixtures("patched_jwks", "fake_model")
async def test_forget_command_is_gone_and_forgets_nothing(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """Sub-plan 4.5, C-5.1 and C-5.2: `/forget` is an unrecognised command, the
    schema has no forgetFromCapture, and the memory stays."""
    user_a, _ = two_users
    headers = _headers(signing_key, settings, user_id=user_a)
    saved = await _submit(client, headers, "/remember Car insurance renews in March")

    typed = (
        await _graphql(
            client,
            headers,
            "mutation($rawInput: String!) { submitCapture(rawInput: $rawInput) { "
            "__typename ... on UnrecognisedCommand { closestMatches } } }",
            {"rawInput": "/forget insurance"},
        )
    )["submitCapture"]
    schema = await client.post(
        "/graphql",
        json={
            "query": "mutation { forgetFromCapture(memoryIds: [], forgetAll: true, "
            "expectedCount: 0) { __typename } }"
        },
        headers=headers,
    )
    still_there = await _graphql(client, headers, "{ memories { id } }")

    assert typed["__typename"] == "UnrecognisedCommand"
    assert "/forget" not in typed["closestMatches"]
    assert "forgetFromCapture" in str(schema.json()["errors"])
    assert [memory["id"] for memory in still_there["memories"]] == [
        saved["memory"]["id"]
    ]
