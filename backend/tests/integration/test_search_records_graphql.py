"""The records view's `search` and a detail's `relatedRecords`, end to end
against a real database. Epic 005, sub-plan 4.3, cases C-3.2 to C-3.5 and
C-3.7. The model is the one thing faked; see search_harness.
"""

import uuid
from typing import Any

import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.settings import Settings
from app.domains.memories.repositories.memory_repository import SqlMemoryRepository
from app.domains.records.repositories.task_repository import SqlTaskRepository
from tests.integration.search_harness import (
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

SEARCH = """
query($text: String!, $recordType: RecordType, $offset: Int!, $limit: Int!) {
  search(text: $text, recordType: $recordType, offset: $offset, limit: $limit) {
    __typename
    ... on SearchPage {
      query
      total
      otherTypesTotal
      meaningUnavailable
      hits {
        __typename
        ... on Task { id }
        ... on Reminder { id }
        ... on Memory { id }
      }
    }
    ... on SearchTooLong { length limit }
  }
}
"""

RELATED = """
query($recordType: RecordType!, $id: ID!) {
  relatedRecords(recordType: $recordType, id: $id) {
    __typename
    ... on Task { id }
    ... on Reminder { id }
    ... on Memory { id }
  }
}
"""


async def search(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    text: str,
    record_type: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> dict[str, Any]:
    data = await graphql(
        client,
        headers,
        SEARCH,
        {"text": text, "recordType": record_type, "offset": offset, "limit": limit},
    )
    page: dict[str, Any] = data["search"]
    return page


async def related_ids(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    record_type: str,
    record_id: uuid.UUID,
) -> list[str]:
    data = await graphql(
        client, headers, RELATED, {"recordType": record_type, "id": str(record_id)}
    )
    return [record["id"] for record in data["relatedRecords"]]


@pytest.mark.usefixtures("patched_jwks", "keyword_embedder")
async def test_the_records_view_finds_what_slash_search_finds(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-3.2, FR-24: the same text, in the same type, the same records."""
    user_id, _ = two_users
    await seed(session_factory=session_factory, user_id=user_id)
    headers = auth_headers(signing_key, settings, user_id=user_id)

    card = await submit(client, headers, "/search passport")
    for group in card["groups"]:
        page = await search(
            client, headers, text="passport", record_type=group["recordType"]
        )
        assert [hit["id"] for hit in page["hits"]][: len(group["hits"])] == [
            hit["record"]["id"] for hit in group["hits"]
        ]
        assert page["total"] == group["total"]

    everything = await search(client, headers, text="passport")
    assert everything["__typename"] == "SearchPage"
    assert everything["total"] == sum(group["total"] for group in card["groups"])
    assert everything["otherTypesTotal"] == 0
    assert everything["meaningUnavailable"] is False


@pytest.mark.usefixtures("patched_jwks", "keyword_embedder")
async def test_a_type_with_no_match_counts_the_other_types(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-3.2: the drawn "No reminders match" state names the others."""
    user_id, _ = two_users
    await seed(session_factory=session_factory, user_id=user_id)
    headers = auth_headers(signing_key, settings, user_id=user_id)

    page = await search(client, headers, text="passport", record_type="REMINDER")

    assert page["hits"] == []
    assert page["total"] == 0
    assert page["otherTypesTotal"] == 2


@pytest.mark.usefixtures("patched_jwks", "keyword_embedder")
async def test_pages_follow_on_from_each_other(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-3.2, the Show more row: the second page is what the first left."""
    user_id, _ = two_users
    await seed(session_factory=session_factory, user_id=user_id)
    headers = auth_headers(signing_key, settings, user_id=user_id)

    whole = await search(client, headers, text="passport")
    first = await search(client, headers, text="passport", limit=1)
    second = await search(client, headers, text="passport", offset=1, limit=1)

    assert [hit["id"] for hit in first["hits"] + second["hits"]] == [
        hit["id"] for hit in whole["hits"]
    ]


@pytest.mark.usefixtures("patched_jwks", "keyword_embedder")
async def test_an_over_long_search_is_refused_with_its_length(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-3.3."""
    user_id, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_id)

    page = await search(client, headers, text="x" * 501)

    assert page == {"__typename": "SearchTooLong", "length": 501, "limit": 500}


@pytest.mark.parametrize(("offset", "limit"), [(-1, 10), (0, 0), (0, 51)])
@pytest.mark.usefixtures("patched_jwks", "keyword_embedder")
async def test_an_offset_or_limit_out_of_range_is_refused(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
    offset: int,
    limit: int,
) -> None:
    """C-3.3: a client bug, so a GraphQL error rather than a union member."""
    user_id, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_id)

    response = await client.post(
        "/graphql",
        json={
            "query": SEARCH,
            "variables": {"text": "passport", "offset": offset, "limit": limit},
        },
        headers=headers,
    )

    assert response.json()["errors"]


@pytest.mark.usefixtures("patched_jwks", "slow_embedder")
async def test_a_slow_meaning_call_still_returns_word_matches_flagged(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-3.4, FR-20."""
    user_id, _ = two_users
    seeded = await seed(session_factory=session_factory, user_id=user_id)
    headers = auth_headers(signing_key, settings, user_id=user_id)

    page = await search(client, headers, text="passport")

    assert page["meaningUnavailable"] is True
    assert {hit["id"] for hit in page["hits"]} == {
        str(seeded["memory"]),
        str(seeded["passport_task"]),
    }


@pytest.mark.usefixtures("patched_jwks")
async def test_the_records_list_no_longer_takes_a_search(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-3.5, FR-22: the letter match is retired from the schema."""
    user_id, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_id)

    response = await client.post(
        "/graphql",
        json={"query": 'query { records(filter: {search: "pass"}) { __typename } }'},
        headers=headers,
    )

    assert response.json()["errors"]


@pytest.mark.usefixtures("patched_jwks", "keyword_embedder")
async def test_related_lists_close_records_of_other_types_but_never_itself(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-3.7, FR-25, FR-26: the passport task and memory are related; the
    Spring Boot task, a different meaning, is not."""
    user_id, _ = two_users
    seeded = await seed(session_factory=session_factory, user_id=user_id)
    headers = auth_headers(signing_key, settings, user_id=user_id)

    from_task = await related_ids(
        client, headers, record_type="TASK", record_id=seeded["passport_task"]
    )
    from_memory = await related_ids(
        client, headers, record_type="MEMORY", record_id=seeded["memory"]
    )
    from_backend = await related_ids(
        client, headers, record_type="TASK", record_id=seeded["backend_task"]
    )

    assert from_task == [str(seeded["memory"])]
    assert from_memory == [str(seeded["passport_task"])]
    assert from_backend == []


@pytest.mark.usefixtures("patched_jwks", "keyword_embedder")
async def test_a_deleted_task_or_forgotten_memory_is_never_related(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-3.7, FR-12."""
    user_id, _ = two_users
    seeded = await seed(session_factory=session_factory, user_id=user_id)
    headers = auth_headers(signing_key, settings, user_id=user_id)

    async with session_factory() as session:
        await SqlMemoryRepository(session).delete_memories(
            user_id=user_id, memory_ids=[seeded["memory"]]
        )
    from_task = await related_ids(
        client, headers, record_type="TASK", record_id=seeded["passport_task"]
    )

    async with session_factory() as session:
        await SqlTaskRepository(session).delete_many(
            user_id=user_id, task_ids=[seeded["passport_task"]]
        )
    from_deleted = await related_ids(
        client, headers, record_type="TASK", record_id=seeded["passport_task"]
    )

    assert from_task == []
    assert from_deleted == []
