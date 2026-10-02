"""Conflicts end to end against a real database, sub-plan 4.3 cases C-3.3,
C-3.5, C-3.6, C-3.8 to C-3.10 and C-3.12.

The model is faked at ``LangChainGeminiProvider``: a candidate contradicts
the fact when both mention an airline. Helpers come from
``test_memories_graphql.py``.
"""

import uuid
from collections.abc import Iterator
from typing import Any

import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql import text

from app.core.settings import Settings, get_settings
from app.domains.gateway.constants import EmbedPurpose
from app.domains.gateway.interfaces.dtos import (
    ExtractionRequest,
    ProviderEmbedding,
    ProviderResult,
)
from app.domains.gateway.services.langchain_provider import LangChainGeminiProvider
from tests.integration.test_forget_graphql import _text_found_anywhere
from tests.integration.test_memories_graphql import (
    _graphql,
    _headers,
    patched_jwks,
    signing_key,
)

__all__ = ["patched_jwks", "signing_key"]

OLD_FACT = "Preferred airline is Emirates"
NEW_FACT = "My preferred airline is Qatar Airways"

SUBMIT = """
mutation($rawInput: String!) {
  submitCapture(rawInput: $rawInput) {
    __typename
    ... on MemorySaved { memory { id text } }
    ... on MemoryConflictAsked {
      pendingCaptureId question newText category conflicting { id text }
    }
  }
}
"""

RESOLVE = """
mutation($id: ID!, $answer: ConflictAnswer!) {
  resolveMemoryConflict(pendingCaptureId: $id, answer: $answer) {
    __typename
    ... on MemorySaved { memory { id text } }
    ... on MemoryDiscarded { message }
    ... on PendingCaptureNotFound { message }
  }
}
"""

HISTORY = """
{ captureHistory { items { inputText outcome forgotten questionText answerText } } }
"""


@pytest.fixture
def conflict_model(monkeypatch: pytest.MonkeyPatch) -> Iterator[list[str]]:
    """Flags every offered candidate that mentions an airline when the fact
    does. Returns the prompts, so a test can see what the model was shown."""
    prompts: list[str] = []

    async def generate(
        self: LangChainGeminiProvider, request: ExtractionRequest
    ) -> ProviderResult:
        prompts.append(request.prompt)
        fact_line, _, candidate_lines = request.prompt.partition("\nCandidates:\n")
        conflicting_ids = [
            line[2:].split(":", 1)[0]
            for line in candidate_lines.splitlines()
            if line.startswith("- ")
            and "airline" in line.lower()
            and "airline" in fact_line.lower()
        ]
        return ProviderResult(
            data={"category": "personal", "conflicting_ids": conflicting_ids},
            input_tokens=150,
            output_tokens=20,
            model="fake-flash",
        )

    async def embed(
        self: LangChainGeminiProvider, *, text: str, purpose: EmbedPurpose
    ) -> ProviderEmbedding:
        return ProviderEmbedding(vector=tuple([0.02] * 768), model="fake-embed")

    monkeypatch.setattr(LangChainGeminiProvider, "generate", generate)
    monkeypatch.setattr(LangChainGeminiProvider, "embed", embed)
    yield prompts


async def _submit(
    client: AsyncClient, headers: dict[str, str], raw_input: str
) -> dict[str, Any]:
    data = await _graphql(client, headers, SUBMIT, {"rawInput": raw_input})
    result: dict[str, Any] = data["submitCapture"]
    return result


async def _resolve(
    client: AsyncClient, headers: dict[str, str], pending_id: str, answer: str
) -> dict[str, Any]:
    data = await _graphql(
        client, headers, RESOLVE, {"id": pending_id, "answer": answer}
    )
    result: dict[str, Any] = data["resolveMemoryConflict"]
    return result


@pytest.mark.usefixtures("patched_jwks", "conflict_model", "job_queue")
async def test_keep_new_replaces_the_old_memory_and_its_history(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """C-3.3, C-3.5 and C-3.8."""
    user_a, _ = two_users
    headers = _headers(signing_key, settings, user_id=user_a)
    old = await _submit(client, headers, f"/remember {OLD_FACT}")

    asked = await _submit(client, headers, f"/remember {NEW_FACT}")
    async with session_factory() as session, session.begin():
        waiting_row = (
            await session.execute(
                text(
                    "SELECT question_text, candidate_text, conflicting_memory_ids "
                    "FROM pending_captures WHERE id = :id"
                ),
                {"id": asked["pendingCaptureId"]},
            )
        ).one()
    resolved = await _resolve(client, headers, asked["pendingCaptureId"], "KEEP_NEW")
    again = await _resolve(client, headers, asked["pendingCaptureId"], "BOTH")
    memories = await _graphql(client, headers, "{ memories { text } }")

    assert asked["__typename"] == "MemoryConflictAsked"
    assert asked["question"] == "Which is correct?"
    assert asked["conflicting"] == [old["memory"]]
    assert waiting_row.question_text == "Which is correct?"
    assert waiting_row.candidate_text == NEW_FACT
    assert [str(memory_id) for memory_id in waiting_row.conflicting_memory_ids] == [
        old["memory"]["id"]
    ]
    assert resolved["__typename"] == "MemorySaved"
    assert again["__typename"] == "PendingCaptureNotFound"
    assert memories["memories"] == [{"text": NEW_FACT}]
    assert await _text_found_anywhere(session_factory, OLD_FACT) == []


@pytest.mark.usefixtures("patched_jwks", "conflict_model", "job_queue")
async def test_forgetting_a_kept_memory_deletes_its_whole_thread(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """C-3.6, FR-23: "Both are correct", then forget the new memory."""
    user_a, _ = two_users
    headers = _headers(signing_key, settings, user_id=user_a)
    await _submit(client, headers, f"/remember {OLD_FACT}")
    asked = await _submit(client, headers, f"/remember {NEW_FACT}")
    kept = await _resolve(client, headers, asked["pendingCaptureId"], "BOTH")

    await _graphql(
        client,
        headers,
        "mutation($id: ID!) { forgetMemory(id: $id) { __typename } }",
        {"id": kept["memory"]["id"]},
    )
    history = await _graphql(client, headers, HISTORY)

    thread = [
        item
        for item in history["captureHistory"]["items"]
        if item["outcome"] in {"QUESTION_ASKED", "MEMORY_CONFLICT_RESOLVED"}
    ]
    # Sub-plan 4.4: the question and the answer are deleted, not blanked.
    assert thread == []
    assert await _text_found_anywhere(session_factory, "Qatar") == []


@pytest.mark.usefixtures("patched_jwks", "conflict_model", "job_queue")
async def test_keep_old_discards_and_an_edit_is_never_checked(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
    conflict_model: list[str],
) -> None:
    """C-3.4 and C-3.9, FR-14."""
    user_a, _ = two_users
    headers = _headers(signing_key, settings, user_id=user_a)
    old = await _submit(client, headers, f"/remember {OLD_FACT}")
    asked = await _submit(client, headers, f"/remember {NEW_FACT}")

    discarded = await _resolve(client, headers, asked["pendingCaptureId"], "KEEP_OLD")
    calls_before_edit = len(conflict_model)
    edited = await _graphql(
        client,
        headers,
        "mutation($id: ID!) { updateMemory(id: $id, input: "
        '{text: "Preferred airline is Qatar Airways", category: PERSONAL}) '
        "{ __typename } }",
        {"id": old["memory"]["id"]},
    )
    memories = await _graphql(client, headers, "{ memories { text } }")

    assert discarded["__typename"] == "MemoryDiscarded"
    assert edited["updateMemory"] == {"__typename": "Memory"}
    assert len(conflict_model) == calls_before_edit
    assert memories["memories"] == [{"text": "Preferred airline is Qatar Airways"}]


@pytest.mark.usefixtures("patched_jwks", "conflict_model", "job_queue")
async def test_users_never_see_or_answer_each_others_conflicts(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
    conflict_model: list[str],
) -> None:
    """C-3.10, NFR-1, T7."""
    user_a, user_b = two_users
    headers_a = _headers(signing_key, settings, user_id=user_a)
    headers_b = _headers(signing_key, settings, user_id=user_b)
    await _submit(client, headers_a, f"/remember {OLD_FACT}")
    asked = await _submit(client, headers_a, f"/remember {NEW_FACT}")

    from_b = await _submit(client, headers_b, f"/remember {NEW_FACT}")
    answered_by_b = await _resolve(
        client, headers_b, asked["pendingCaptureId"], "KEEP_NEW"
    )
    a_memories = await _graphql(client, headers_a, "{ memories { text } }")

    assert from_b["__typename"] == "MemorySaved"
    assert OLD_FACT not in conflict_model[-1]
    assert answered_by_b["__typename"] == "PendingCaptureNotFound"
    assert a_memories["memories"] == [{"text": OLD_FACT}]


@pytest.mark.usefixtures("patched_jwks", "conflict_model", "job_queue")
async def test_an_answer_works_with_the_gateway_switched_off(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
    session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """C-3.12 and Q1: saved without a vector, and the reembed job queued."""
    user_a, _ = two_users
    headers = _headers(signing_key, settings, user_id=user_a)
    await _submit(client, headers, f"/remember {OLD_FACT}")
    asked = await _submit(client, headers, f"/remember {NEW_FACT}")
    monkeypatch.setattr(get_settings(), "gateway_enabled", False)

    kept = await _resolve(client, headers, asked["pendingCaptureId"], "BOTH")
    async with session_factory() as session, session.begin():
        vector_is_null = await session.scalar(
            text("SELECT embedding IS NULL FROM memories WHERE id = :id"),
            {"id": kept["memory"]["id"]},
        )
        await session.execute(text("SET LOCAL search_path TO procrastinate"))
        queued = await session.scalar(
            text(
                "SELECT count(*) FROM procrastinate.procrastinate_jobs "
                "WHERE task_name = 'memories.reembed' AND args->>'memory_id' = :id"
            ),
            {"id": kept["memory"]["id"]},
        )

    assert kept["__typename"] == "MemorySaved"
    assert vector_is_null is True
    assert queued == 1
