"""Epic 005, sub-plan 4.1, C-11: rule T7 for search. User B searches with
user A's exact words, and with the same meaning, and gets none of A's
records, through the whole stack under Row Level Security (NFR-1)."""

import uuid
from typing import Any

import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.settings import Settings
from tests.integration.search_harness import (
    auth_headers,
    keyword_embedder,
    patched_jwks,
    seed,
    signing_key,
    submit,
)

__all__ = ["keyword_embedder", "patched_jwks", "signing_key"]


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
