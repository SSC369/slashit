"""NFR-6 and NFR-7, sub-plan 4.1 case C-15: search quality against the real
embedding model, and the evidence for tuning MEANING_MAX_DISTANCE (AD-3).

Seeds ``tests/eval/search_queries.json``'s records for one user, embedding
each through the gateway as the embed jobs would, then ranks every query
across all three record types exactly as a search does. Spends well under a
cent. Runs locally, never in CI, per the `live` marker (004 04.3 Q4).
"""

import json
import pathlib
import uuid
from datetime import UTC, date, datetime, time, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.deps import build_embed_interactor, build_search_service
from app.core.settings import Settings
from app.domains.gateway.public import Embedding
from app.domains.memories.interfaces.repositories import MemoryWrite
from app.domains.memories.repositories.memory_repository import SqlMemoryRepository
from app.domains.records.repositories.task_repository import SqlTaskRepository
from app.domains.reminders.interfaces.repositories import ReminderWrite
from app.domains.reminders.repositories.reminder_repository import (
    SqlReminderRepository,
)
from app.domains.reminders.services.schedule import RepeatKind, ScheduleSpec
from app.domains.search.constants import MEANING_MAX_DISTANCE, PORT_LIMIT
from app.domains.search.services.ranking import rank_key
from app.domains.search.services.terms import build_terms

EVAL_SET = pathlib.Path(__file__).parent.parent / "eval" / "search_queries.json"
WORD_TARGET = 0.95
MEANING_TARGET = 0.80


class _JobContext:
    """What build_search_service reads from a request context."""

    def __init__(
        self,
        *,
        session: AsyncSession,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self.session = session
        self.session_factory = session_factory


def _reminder_write(*, description: str) -> ReminderWrite:
    return ReminderWrite(
        description=description,
        spec=ScheduleSpec(
            repeat_kind=RepeatKind.NONE,
            repeat_interval=1,
            repeat_weekdays=(),
            repeat_month_day=None,
            local_time=time(9, 0),
            anchor_local_date=date(2026, 12, 1),
            one_time_at=datetime(2026, 12, 1, 9, 0, tzinfo=UTC),
        ),
        schedule_timezone="UTC",
        next_fire_at=datetime.now(UTC) + timedelta(days=60),
        state="upcoming",
    )


async def _seed(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
    user_id: uuid.UUID,
    records: list[dict[str, str]],
) -> dict[uuid.UUID, str]:
    """Creates every record with its real vector. Returns record id to key."""
    embed = build_embed_interactor(session_factory=session_factory, settings=settings)
    keys: dict[uuid.UUID, str] = {}
    async with session_factory() as session:
        tasks = SqlTaskRepository(session)
        reminders = SqlReminderRepository(session)
        memories = SqlMemoryRepository(session)
        for record in records:
            embedding = await embed.embed(user_id=user_id, text=record["text"])
            assert isinstance(embedding, Embedding), embedding
            if record["type"] == "task":
                task = await tasks.create_task(
                    user_id=user_id,
                    title=record["text"],
                    due_at=None,
                    origin="command",
                    original_input=None,
                )
                await tasks.set_embedding(
                    user_id=user_id,
                    task_id=task.id,
                    title=task.title,
                    embedding=embedding.vector,
                )
                keys[task.id] = record["key"]
            elif record["type"] == "reminder":
                reminder = await reminders.create_reminder(
                    user_id=user_id,
                    write=_reminder_write(description=record["text"]),
                    origin="command",
                    original_input=None,
                )
                await reminders.set_embedding(
                    user_id=user_id,
                    reminder_id=reminder.id,
                    description=reminder.description,
                    embedding=embedding.vector,
                )
                keys[reminder.id] = record["key"]
            else:
                memory = await memories.create_memory(
                    user_id=user_id,
                    write=MemoryWrite(
                        text=record["text"],
                        category=None,
                        embedding=embedding.vector,
                        origin="command",
                        original_input=None,
                    ),
                )
                keys[memory.id] = record["key"]
    return keys


@pytest.mark.live
async def test_search_quality_meets_nfr_6_and_nfr_7(
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    eval_user: uuid.UUID,
) -> None:
    user_id = eval_user
    eval_set = json.loads(EVAL_SET.read_text())
    keys = await _seed(
        session_factory=session_factory,
        settings=settings,
        user_id=user_id,
        records=eval_set["records"],
    )

    async def ranked_keys(query: str) -> tuple[list[str], dict[str, float | None]]:
        async with session_factory() as session:
            service = build_search_service(
                _JobContext(session=session, session_factory=session_factory)  # type: ignore[arg-type]
            )
            vector = await service.query_embedding.embed_query(
                user_id=user_id, text=query
            )
            candidates = []
            for port in service.search_ports:
                page = await port.search_candidates(
                    user_id=user_id,
                    terms=build_terms(text=query),
                    query_embedding=vector,
                    max_distance=MEANING_MAX_DISTANCE,
                    limit=PORT_LIMIT,
                )
                candidates.extend(page.candidates)
        ordered = sorted(candidates, key=rank_key)
        distances = {keys[item.record_id]: item.distance for item in ordered}
        return [keys[item.record_id] for item in ordered], distances

    word_misses: list[str] = []
    for case in eval_set["word_queries"]:
        ranked, _ = await ranked_keys(case["query"])
        if case["expected"] not in ranked[:3]:
            word_misses.append(
                f"{case['query']!r}: {case['expected']} not in {ranked[:3]}"
            )

    meaning_misses: list[str] = []
    for case in eval_set["meaning_queries"]:
        ranked, distances = await ranked_keys(case["query"])
        if case["expected"] not in ranked[:5]:
            meaning_misses.append(
                f"{case['query']!r}: {case['expected']} "
                f"(distance {distances.get(case['expected'])}) not in {ranked[:5]}"
            )

    word_rate = 1 - len(word_misses) / len(eval_set["word_queries"])
    meaning_rate = 1 - len(meaning_misses) / len(eval_set["meaning_queries"])
    print(f"NFR-6 word queries: {word_rate:.0%} in the top three")
    for miss in word_misses:
        print("  miss:", miss)
    print(
        f"NFR-7 meaning queries: {meaning_rate:.0%} in the top five "
        f"at MEANING_MAX_DISTANCE {MEANING_MAX_DISTANCE}"
    )
    for miss in meaning_misses:
        print("  miss:", miss)
    assert word_rate > WORD_TARGET
    assert meaning_rate > MEANING_TARGET
