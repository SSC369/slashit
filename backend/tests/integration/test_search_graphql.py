"""`/search` end to end against a real database: schema, auth, resolver, deps,
capture, search, the three record domains, full-text search, pgvector and RLS.

Epic 005, sub-plan 4.1, cases C-5 to C-7 through GraphQL, plus the FR-1 to
FR-12 and FR-20 paths. The model is the one thing faked; see search_harness.
"""

import uuid
from typing import Any

import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.settings import Settings
from tests.integration.search_harness import (
    ANSWER,
    HISTORY,
    auth_headers,
    graphql,
    keyword_embedder,
    patched_jwks,
    seed,
    signing_key,
    slow_embedder,
    submit,
)

__all__ = ["keyword_embedder", "patched_jwks", "signing_key", "slow_embedder"]


def hit_ids(result: dict[str, Any]) -> dict[str, list[str]]:
    return {
        group["recordType"]: [hit["record"]["id"] for hit in group["hits"]]
        for group in result["groups"]
    }


@pytest.mark.usefixtures("patched_jwks", "keyword_embedder")
async def test_search_groups_records_of_every_type_by_word(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """FR-1, FR-4, FR-7, FR-9: `/search passport` finds the memory and the
    task, each under its own type."""
    user_id, _ = two_users
    seeded = await seed(session_factory=session_factory, user_id=user_id)
    headers = auth_headers(signing_key, settings, user_id=user_id)

    result = await submit(client, headers, "/search passport")

    assert result["__typename"] == "SearchResults"
    assert result["query"] == "passport"
    assert result["meaningUnavailable"] is False
    ids = hit_ids(result)
    assert ids["MEMORY"] == [str(seeded["memory"])]
    assert ids["TASK"][0] == str(seeded["passport_task"])
    assert str(seeded["backend_task"]) not in ids["TASK"]
    assert all(
        hit["citation"] is None for group in result["groups"] for hit in group["hits"]
    )


@pytest.mark.usefixtures("patched_jwks", "keyword_embedder")
async def test_search_finds_a_record_by_meaning_with_no_shared_word(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """FR-5, US-2: "career" finds the Spring Boot task."""
    user_id, _ = two_users
    seeded = await seed(session_factory=session_factory, user_id=user_id)
    headers = auth_headers(signing_key, settings, user_id=user_id)

    result = await submit(client, headers, "/search career")

    assert hit_ids(result)["TASK"] == [str(seeded["backend_task"])]


@pytest.mark.usefixtures("patched_jwks", "slow_embedder")
async def test_a_slow_meaning_call_still_returns_word_matches_flagged(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """FR-20, AD-4: past the budget, word matches return with the flag."""
    user_id, _ = two_users
    seeded = await seed(session_factory=session_factory, user_id=user_id)
    headers = auth_headers(signing_key, settings, user_id=user_id)

    result = await submit(client, headers, "/search passport")

    assert result["meaningUnavailable"] is True
    assert str(seeded["passport_task"]) in hit_ids(result)["TASK"]


@pytest.mark.usefixtures("patched_jwks", "keyword_embedder")
async def test_nothing_found_returns_no_groups(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """FR-10."""
    user_id, _ = two_users
    await seed(session_factory=session_factory, user_id=user_id)
    headers = auth_headers(signing_key, settings, user_id=user_id)

    result = await submit(client, headers, "/search kayak")

    assert result["__typename"] == "SearchResults"
    assert result["groups"] == []


@pytest.mark.usefixtures("patched_jwks", "keyword_embedder")
async def test_an_over_long_search_is_refused_with_its_length(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-6, FR-3: over 500 characters of search text is a drawn state, not a
    client error, though the whole line is over capture's usual cap."""
    user_id, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_id)

    result = await submit(client, headers, "/search " + "a" * 501)

    assert result == {"__typename": "SearchTooLong", "length": 501, "limit": 500}


@pytest.mark.usefixtures("patched_jwks", "keyword_embedder")
async def test_an_empty_search_asks_and_the_answer_runs_the_search(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-5, FR-2, and C-7, FR-21: the answered search is kept in history as
    its whole line, so Run again repeats it."""
    user_id, _ = two_users
    await seed(session_factory=session_factory, user_id=user_id)
    headers = auth_headers(signing_key, settings, user_id=user_id)

    asked = await submit(client, headers, "/search")
    assert asked["__typename"] == "PendingQuestionCreated"
    assert asked["question"] == "What should Slashit search for?"

    answered = await graphql(
        client,
        headers,
        ANSWER,
        {"id": asked["pendingCaptureId"], "answer": "passport"},
    )
    assert answered["answerPendingCapture"]["__typename"] == "SearchResults"
    assert answered["answerPendingCapture"]["query"] == "passport"

    await submit(client, headers, "/search visa")
    history = await graphql(client, headers, HISTORY)
    searched = [
        item["inputText"]
        for item in history["captureHistory"]["items"]
        if item["outcome"] == "SEARCHED"
    ]
    assert set(searched) == {"/search passport", "/search visa"}


@pytest.mark.usefixtures("patched_jwks", "keyword_embedder")
async def test_a_search_is_logged_as_an_event_with_no_text(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """PRD section 8: one `search_run` event per search (AD-10: no text)."""
    from sqlalchemy import func, select

    from app.domains.analytics.models import Event

    user_id, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_id)

    await submit(client, headers, "/search passport")

    async with session_factory() as session:
        count = await session.scalar(
            select(func.count())
            .select_from(Event)
            .where(Event.user_id == user_id, Event.event_type == "search_run")
        )
    assert count == 1
