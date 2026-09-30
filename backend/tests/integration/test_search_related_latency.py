"""NFR-5, sub-plan 4.3 case C-3.12: a related list's time at 3,000 records.

Related records call no model (AD-6), so unlike the other latency cases this
one runs without a provider key. Marked `live` all the same: it is a timing,
and a shared CI runner would make it flaky.
"""

import random
import statistics
import time
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.deps import build_search_service
from app.domains.records.models import Task
from app.domains.search.interfaces.dtos import RecordType
from tests.integration.test_search_latency_live import (
    RECORDS_PER_TYPE,
    _JobContext,
    _seed_three_thousand_records,
)

RUNS = 20
TARGET_P95_SECONDS = 1.0


@pytest.mark.live
async def test_a_related_list_at_three_thousand_records_meets_nfr_5(
    session_factory: async_sessionmaker[AsyncSession],
    eval_user: uuid.UUID,
) -> None:
    user_id = eval_user
    await _seed_three_thousand_records(session_factory=session_factory, user_id=user_id)
    async with session_factory() as session:
        task_ids = list(
            (
                await session.scalars(select(Task.id).where(Task.user_id == user_id))
            ).all()
        )
    rng = random.Random(7)

    timings: list[float] = []
    for _ in range(RUNS):
        async with session_factory() as session:
            service = build_search_service(
                _JobContext(session=session, session_factory=session_factory)  # type: ignore[arg-type]
            )
            started = time.monotonic()
            await service.related(
                user_id=user_id,
                record_type=RecordType.TASK,
                record_id=rng.choice(task_ids),
            )
            timings.append(time.monotonic() - started)

    p95 = statistics.quantiles(timings, n=20)[-1]
    median = statistics.median(timings)
    print(
        f"NFR-5 at {RECORDS_PER_TYPE * 2} records: median {median:.3f}s, "
        f"p95 {p95:.3f}s over {RUNS} related lists"
    )
    assert p95 < TARGET_P95_SECONDS
