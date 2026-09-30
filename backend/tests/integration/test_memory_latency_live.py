"""NFR-4 against the real model: a save under 8 s at p95 with 1,000 memories.

Each save is timed end to end through GraphQL: the embed, the candidate search
over 1,000 vectors, the judgement with ten candidates, and the writes. Runs
locally, never in CI, per the `live` marker. Spends a fraction of a cent.
"""

import statistics
import time
import uuid

import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql import text

from app.core.db import user_transaction
from app.core.settings import Settings
from tests.integration.test_memories_graphql import (
    _headers,
    _submit,
    patched_jwks,
    signing_key,
)

__all__ = ["patched_jwks", "signing_key"]

SAVES = 20
TARGET_P95_SECONDS = 8.0
FACTS = [f"My test locker number at gym branch {n} is {1000 + n}" for n in range(SAVES)]


@pytest.mark.live
@pytest.mark.usefixtures("patched_jwks")
async def test_save_latency_meets_nfr_4(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    eval_user: uuid.UUID,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with (
        session_factory() as session,
        user_transaction(session, eval_user) as scoped,
    ):
        # One random vector shared by all rows is enough: the candidate search
        # still ranks 1,000 of them.
        await scoped.execute(
            text(
                "INSERT INTO memories (id, user_id, text, category, origin, "
                "embedding, created_at, updated_at) "
                "SELECT gen_random_uuid(), :u, "
                "'Seeded fact ' || n || ' about travel and family plans', "
                "'life', 'command', v.vec, now(), now() "
                "FROM generate_series(1, 1000) n, "
                "(SELECT array_agg(random())::vector(768) AS vec "
                "FROM generate_series(1, 768)) v"
            ),
            {"u": eval_user},
        )
    headers = _headers(signing_key, settings, user_id=eval_user)

    timings: list[float] = []
    outcomes: list[str] = []
    for fact in FACTS:
        started = time.perf_counter()
        result = await _submit(client, headers, f"/remember {fact}")
        timings.append(time.perf_counter() - started)
        outcomes.append(result["__typename"])

    p95 = statistics.quantiles(timings, n=20)[-1]
    print(
        f"NFR-4 save p95 {p95:.2f} s, median {statistics.median(timings):.2f} s, "
        f"max {max(timings):.2f} s over {SAVES} saves"
    )
    print("outcomes:", {name: outcomes.count(name) for name in set(outcomes)})
    assert p95 < TARGET_P95_SECONDS
