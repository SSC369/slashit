"""Forget end to end against a real database, sub-plan 4.2 cases C-2.1 to
C-2.3, C-2.6 to C-2.10 and C-2.12. NFR-2's search-every-table case is C-2.9.

The model is faked at ``LangChainGeminiProvider``, as in
``test_memories_graphql.py``, whose fixtures and helpers this reuses.
"""

import uuid
from typing import Any

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

FORGET_OFFER = """
mutation($rawInput: String!) {
  submitCapture(rawInput: $rawInput) {
    __typename
    ... on ForgetCandidates {
      searchText totalMatches forgetAll allCount candidates { id text }
    }
  }
}
"""

CONFIRM = """
mutation($ids: [ID!]!, $all: Boolean!, $expected: Int!) {
  forgetFromCapture(memoryIds: $ids, forgetAll: $all, expectedCount: $expected) {
    __typename
    ... on MemoriesForgotten { count }
    ... on MemoryCountChanged { count message }
  }
}
"""

HISTORY = """
{ captureHistory { items { inputText outcome forgotten affectedCount answerText } } }
"""

FACT = "My passport number is P7788123"


async def _offer(
    client: AsyncClient, headers: dict[str, str], raw_input: str
) -> dict[str, Any]:
    data = await _graphql(client, headers, FORGET_OFFER, {"rawInput": raw_input})
    result: dict[str, Any] = data["submitCapture"]
    return result


async def _confirm(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    ids: list[str],
    forget_all: bool = False,
    expected: int = 0,
) -> dict[str, Any]:
    data = await _graphql(
        client, headers, CONFIRM, {"ids": ids, "all": forget_all, "expected": expected}
    )
    result: dict[str, Any] = data["forgetFromCapture"]
    return result


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
    forgotten_turns = [
        item for item in history["captureHistory"]["items"] if item["forgotten"]
    ]
    assert len(forgotten_turns) == 2
    assert all(item["inputText"] == "" for item in forgotten_turns)
    assert all(item["answerText"] is None for item in forgotten_turns)
    async with session_factory() as session, session.begin():
        tombstone = (
            await session.execute(
                text(
                    "SELECT deleted_at IS NOT NULL, text, original_input, category, "
                    "embedding FROM memories WHERE id = :id"
                ),
                {"id": first_id},
            )
        ).one()
    assert tombstone == (True, None, None, None, None)
    assert await _text_found_anywhere(session_factory, "P7788123") == []


@pytest.mark.usefixtures("patched_jwks", "fake_model")
async def test_forget_by_command_picks_confirms_and_logs_only_the_count(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-2.4, C-2.5 and C-2.8 through GraphQL."""
    user_a, _ = two_users
    headers = _headers(signing_key, settings, user_id=user_a)
    await _submit(client, headers, "/remember Preferred airline is Emirates")
    await _submit(client, headers, "/remember Airline miles number is EK 204")
    await _submit(client, headers, "/remember Mom's birthday is October 12")

    offered = await _offer(client, headers, "/forget airline")
    nothing = await _offer(client, headers, "/forget visa")
    confirmed = await _confirm(client, headers, ids=[offered["candidates"][0]["id"]])
    history = await _graphql(client, headers, HISTORY)

    assert offered["totalMatches"] == 2
    assert len(offered["candidates"]) == 2
    assert nothing["candidates"] == []
    assert confirmed == {"__typename": "MemoriesForgotten", "count": 1}
    newest = history["captureHistory"]["items"][0]
    assert newest["inputText"] == "/forget"
    assert newest["outcome"] == "MEMORY_FORGOTTEN"
    assert newest["affectedCount"] == 1
    assert not any(
        "airline" in item["inputText"] and item["inputText"].startswith("/forget")
        for item in history["captureHistory"]["items"]
    )


@pytest.mark.usefixtures("patched_jwks", "fake_model")
async def test_forget_all_confirms_the_count(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-2.6 and C-2.7."""
    user_a, _ = two_users
    headers = _headers(signing_key, settings, user_id=user_a)
    await _submit(client, headers, "/remember One fact")
    await _submit(client, headers, "/remember Another fact")

    offered = await _offer(client, headers, "/forget all my memories")
    stale = await _confirm(client, headers, ids=[], forget_all=True, expected=1)
    done = await _confirm(client, headers, ids=[], forget_all=True, expected=2)
    left = await _graphql(client, headers, "{ memories { id } }")

    assert offered["forgetAll"] is True
    assert offered["allCount"] == 2
    assert stale["__typename"] == "MemoryCountChanged"
    assert stale["count"] == 2
    assert done == {"__typename": "MemoriesForgotten", "count": 2}
    assert left["memories"] == []


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
    from_capture = await _confirm(client, headers_b, ids=[memory_id])
    still_there = await _graphql(client, headers_a, "{ memories { id } }")

    assert from_records["forgetMemory"] == {"__typename": "MemoryNotFound"}
    assert from_capture["__typename"] == "ForgetTargetGone"
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

    offered = await _offer(client, headers, "/forget insurance")
    confirmed = await _confirm(client, headers, ids=[saved["memory"]["id"]])

    assert len(offered["candidates"]) == 1
    assert confirmed == {"__typename": "MemoriesForgotten", "count": 1}
