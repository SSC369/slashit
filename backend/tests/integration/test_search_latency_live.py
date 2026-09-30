"""NFR-3, sub-plan 4.1 case C-14: a search's time at 3,000 records, against
the real embedding model. Records are seeded with stored vectors directly, so
only the searches call the model. Runs locally, never in CI (`live`).

From a dev machine this measures the network to the provider and to the
database as well; the PRD re-measures NFR-3 from the deployed API (epic 012).
"""

import random
import statistics
import time
import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.deps import build_search_service
from app.core.settings import Settings
from app.domains.memories.models import Memory
from app.domains.records.models import Task

RECORDS_PER_TYPE = 1500
RUNS = 20
TARGET_P95_SECONDS = 3.0
QUERIES = ["passport", "career", "rent", "insurance", "what am I learning"]


class _JobContext:
    def __init__(
        self,
        *,
        session: AsyncSession,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self.session = session
        self.session_factory = session_factory


def _random_unit_vector(*, rng: random.Random) -> list[float]:
    raw = [rng.gauss(0, 1) for _ in range(768)]
    norm = sum(value * value for value in raw) ** 0.5
    return [value / norm for value in raw]


@pytest.mark.live
async def test_a_search_at_three_thousand_records_meets_nfr_3(
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    eval_user: uuid.UUID,
) -> None:
    """1,500 tasks and 1,500 memories: 3,000 records, `estimate` of a heavy
    V1 user (PRD NFR-3 assumption)."""
    user_id = eval_user
    rng = random.Random(5)
    now = datetime.now(UTC)
    async with session_factory() as session, session.begin():
        await session.execute(
            insert(Task),
            [
                {
                    "id": uuid.uuid4(),
                    "user_id": user_id,
                    "title": f"Task {index} about topic {index % 97}",
                    "status": "pending",
                    "origin": "command",
                    "created_at": now,
                    "updated_at": now,
                    "embedding": _random_unit_vector(rng=rng),
                }
                for index in range(RECORDS_PER_TYPE)
            ],
        )
        await session.execute(
            insert(Memory),
            [
                {
                    "id": uuid.uuid4(),
                    "user_id": user_id,
                    "text": f"Memory {index} about topic {index % 89}",
                    "origin": "command",
                    "created_at": now,
                    "updated_at": now,
                    "embedding": _random_unit_vector(rng=rng),
                }
                for index in range(RECORDS_PER_TYPE)
            ],
        )

    timings: list[float] = []
    for run in range(RUNS):
        async with session_factory() as session:
            service = build_search_service(
                _JobContext(session=session, session_factory=session_factory)  # type: ignore[arg-type]
            )
            started = time.monotonic()
            results = await service.search_for_capture(
                user_id=user_id, text=QUERIES[run % len(QUERIES)]
            )
            timings.append(time.monotonic() - started)
            assert results.meaning_unavailable is False

    p95 = statistics.quantiles(timings, n=20)[-1]
    median = statistics.median(timings)
    print(
        f"NFR-3 at {RECORDS_PER_TYPE * 2} records: median {median:.2f}s, "
        f"p95 {p95:.2f}s over {RUNS} runs"
    )
    assert p95 < TARGET_P95_SECONDS
