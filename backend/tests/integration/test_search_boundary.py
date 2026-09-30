"""Epic 005, sub-plans 4.1 to 4.3, C-11, C-2.10 and C-3.8: rule T7 for
search. User B searches with user A's exact words, and with the same meaning,
asks for A's record's related list by its id, and gets none of A's records,
through the whole stack under Row Level Security (NFR-1)."""

import uuid
from typing import Any

import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.settings import Settings
from tests.integration.search_harness import (
    answering_model,
    auth_headers,
    graphql,
    keyword_embedder,
    patched_jwks,
    seed,
    signing_key,
    submit,
)

__all__ = ["answering_model", "keyword_embedder", "patched_jwks", "signing_key"]


def _all_ids(result: dict[str, Any]) -> set[str]:
    return {hit["record"]["id"] for group in result["groups"] for hit in group["hits"]}


@pytest.mark.usefixtures("patched_jwks", "keyword_embedder")
async def test_user_b_never_sees_user_a_records_by_word_or_meaning(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    user_a, user_b = two_users
    seeded = await seed(session_factory=session_factory, user_id=user_a)
    headers_b = auth_headers(signing_key, settings, user_id=user_b)

    by_exact_title = await submit(client, headers_b, "/search Renew passport")
    by_meaning = await submit(client, headers_b, "/search career")

    a_ids = {str(record_id) for record_id in seeded.values()}
    assert by_exact_title["groups"] == []
    assert by_meaning["groups"] == []
    assert not (_all_ids(by_exact_title) | _all_ids(by_meaning)) & a_ids


@pytest.mark.usefixtures("patched_jwks", "keyword_embedder")
async def test_user_a_still_finds_their_own_records(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """The control for the case above: the same search, as the owner."""
    user_a, _ = two_users
    seeded = await seed(session_factory=session_factory, user_id=user_a)
    headers_a = auth_headers(signing_key, settings, user_id=user_a)

    result = await submit(client, headers_a, "/search Renew passport")

    assert str(seeded["passport_task"]) in _all_ids(result)


@pytest.mark.usefixtures("patched_jwks", "keyword_embedder")
async def test_user_b_question_never_puts_user_a_records_in_the_prompt(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
    answering_model: list[str],
) -> None:
    """C-2.10, NFR-1, T7: B asks about A's passport. A's words never reach a
    model prompt, and with no records of B's own there is no model call."""
    user_a, user_b = two_users
    await seed(session_factory=session_factory, user_id=user_a)
    headers_b = auth_headers(signing_key, settings, user_id=user_b)

    result = await submit(client, headers_b, "/search when does my passport expire?")

    assert result["noSupport"] is True
    assert not any("passport" in prompt.lower() for prompt in answering_model)


RECORDS_SEARCH = """
query($text: String!) {
  search(text: $text) {
    ... on SearchPage { hits { ... on Task { id } ... on Memory { id } } }
  }
}
"""

RELATED = """
query($recordType: RecordType!, $id: ID!) {
  relatedRecords(recordType: $recordType, id: $id) {
    ... on Task { id }
    ... on Reminder { id }
    ... on Memory { id }
  }
}
"""


@pytest.mark.usefixtures("patched_jwks", "keyword_embedder")
async def test_user_b_records_search_and_related_never_reach_user_a(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-3.8, NFR-1, T7: B holds the same records as A, so every match and
    every neighbour exists in both accounts. B sees only B's, and A's ids
    give B nothing."""
    user_a, user_b = two_users
    seeded_a = await seed(session_factory=session_factory, user_id=user_a)
    seeded_b = await seed(session_factory=session_factory, user_id=user_b)
    headers_b = auth_headers(signing_key, settings, user_id=user_b)
    ids_a = {str(record_id) for record_id in seeded_a.values()}

    page = await graphql(client, headers_b, RECORDS_SEARCH, {"text": "passport"})
    own_related = await graphql(
        client,
        headers_b,
        RELATED,
        {"recordType": "TASK", "id": str(seeded_b["passport_task"])},
    )
    a_related = await graphql(
        client,
        headers_b,
        RELATED,
        {"recordType": "TASK", "id": str(seeded_a["passport_task"])},
    )

    found = {hit["id"] for hit in page["search"]["hits"]}
    assert found == {str(seeded_b["memory"]), str(seeded_b["passport_task"])}
    assert found.isdisjoint(ids_a)
    assert [record["id"] for record in own_related["relatedRecords"]] == [
        str(seeded_b["memory"])
    ]
    assert a_related["relatedRecords"] == []
