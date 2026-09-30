"""Epic 005, sub-plan 4.1, C-8: each record domain's search query against a
real database. Word match, meaning match, deleted row excluded, total, and
the vector cleared by an edit that changes the text (FR-4, FR-5, FR-12, FR-14).
"""

import uuid
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.memories.interfaces.repositories import MemoryWrite
from app.domains.memories.repositories.memory_repository import SqlMemoryRepository
from app.domains.records.repositories.task_repository import SqlTaskRepository
from app.domains.reminders.interfaces.repositories import ReminderWrite
from app.domains.reminders.repositories.reminder_repository import (
    SqlReminderRepository,
)
from app.domains.reminders.services.schedule import RepeatKind, ScheduleSpec

DIMENSIONS = 768
MAX_DISTANCE = 0.35


def _axis_vector(*, axis: int) -> tuple[float, ...]:
    """A unit vector along one axis: distance 0 to itself, 1 to any other."""
    return tuple(1.0 if index == axis else 0.0 for index in range(DIMENSIONS))


def _reminder_write(*, description: str) -> ReminderWrite:
    return ReminderWrite(
        description=description,
        spec=ScheduleSpec(
            repeat_kind=RepeatKind.NONE,
            repeat_interval=1,
            repeat_weekdays=(),
            repeat_month_day=None,
            local_time=time(9, 0),
            anchor_local_date=date(2026, 10, 10),
            one_time_at=datetime(2026, 10, 10, 9, 0, tzinfo=UTC),
        ),
        schedule_timezone="UTC",
        next_fire_at=datetime.now(UTC) + timedelta(days=10),
        state="upcoming",
    )


async def test_task_search_matches_by_word_and_by_meaning(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    user_id, _ = two_users
    async with session_factory() as session:
        repository = SqlTaskRepository(session)
        by_word = await repository.create_task(
            user_id=user_id,
            title="Renew passport",
            due_at=None,
            origin="command",
            original_input=None,
        )
        by_meaning = await repository.create_task(
            user_id=user_id,
            title="Build a REST API",
            due_at=None,
            origin="command",
            original_input=None,
        )
        unrelated = await repository.create_task(
            user_id=user_id,
            title="Buy milk",
            due_at=None,
            origin="command",
            original_input=None,
        )
        deleted = await repository.create_task(
            user_id=user_id,
            title="Passport photos",
            due_at=None,
            origin="command",
            original_input=None,
        )
        for task, axis in ((by_meaning, 0), (unrelated, 1)):
            await repository.set_embedding(
                user_id=user_id,
                task_id=task.id,
                title=task.title,
                embedding=_axis_vector(axis=axis),
            )
        await repository.delete_many(user_id=user_id, task_ids=[deleted.id])

        word_page = await repository.search_tasks(
            user_id=user_id,
            terms=["passport"],
            query_embedding=None,
            max_distance=MAX_DISTANCE,
            limit=50,
        )
        meaning_page = await repository.search_tasks(
            user_id=user_id,
            terms=[],
            query_embedding=_axis_vector(axis=0),
            max_distance=MAX_DISTANCE,
            limit=50,
        )

    assert [match.task.id for match in word_page.matches] == [by_word.id]
    assert word_page.total == 1
    assert word_page.matches[0].all_terms is True
    assert word_page.matches[0].word_rank is not None
    assert word_page.matches[0].distance is None

    assert [match.task.id for match in meaning_page.matches] == [by_meaning.id]
    assert meaning_page.matches[0].word_rank is None
    assert meaning_page.matches[0].distance is not None
    assert meaning_page.matches[0].distance < 0.01


async def test_task_all_terms_is_false_when_only_some_terms_match(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    user_id, _ = two_users
    async with session_factory() as session:
        repository = SqlTaskRepository(session)
        both = await repository.create_task(
            user_id=user_id,
            title="Renew passport online",
            due_at=None,
            origin="command",
            original_input=None,
        )
        one = await repository.create_task(
            user_id=user_id,
            title="Renew insurance",
            due_at=None,
            origin="command",
            original_input=None,
        )
        page = await repository.search_tasks(
            user_id=user_id,
            terms=["renew", "passport"],
            query_embedding=None,
            max_distance=MAX_DISTANCE,
            limit=50,
        )

    by_id = {match.task.id: match for match in page.matches}
    assert by_id[both.id].all_terms is True
    assert by_id[one.id].all_terms is False
    assert page.total == 2


async def test_a_title_edit_clears_the_vector_and_an_unchanged_title_keeps_it(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    user_id, _ = two_users
    async with session_factory() as session:
        repository = SqlTaskRepository(session)
        task = await repository.create_task(
            user_id=user_id,
            title="Renew passport",
            due_at=None,
            origin="command",
            original_input=None,
        )
        await repository.set_embedding(
            user_id=user_id,
            task_id=task.id,
            title=task.title,
            embedding=_axis_vector(axis=0),
        )
        await repository.update(
            user_id=user_id,
            task_id=task.id,
            title="Renew passport",
            status=None,
            due_at=None,
            due_at_provided=False,
        )
        kept = await repository.get_embedding(user_id=user_id, task_id=task.id)
        await repository.update(
            user_id=user_id,
            task_id=task.id,
            title="Renew driving licence",
            status=None,
            due_at=None,
            due_at_provided=False,
        )
        cleared = await repository.get_embedding(user_id=user_id, task_id=task.id)
        stale_write = await repository.set_embedding(
            user_id=user_id,
            task_id=task.id,
            title="Renew passport",
            embedding=_axis_vector(axis=0),
        )

    assert kept is not None
    assert cleared is None
    # A vector computed for the old title is refused after the edit.
    assert stale_write is False


async def test_reminder_search_matches_and_skips_deleted(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    user_id, _ = two_users
    async with session_factory() as session:
        repository = SqlReminderRepository(session)
        live = await repository.create_reminder(
            user_id=user_id,
            write=_reminder_write(description="Check passport renewal requirements"),
            origin="command",
            original_input=None,
        )
        gone = await repository.create_reminder(
            user_id=user_id,
            write=_reminder_write(description="Collect passport"),
            origin="command",
            original_input=None,
        )
        await repository.set_embedding(
            user_id=user_id,
            reminder_id=live.id,
            description=live.description,
            embedding=_axis_vector(axis=2),
        )
        await repository.soft_delete(user_id=user_id, reminder_id=gone.id)
        word_page = await repository.search_reminders(
            user_id=user_id,
            terms=["passport"],
            query_embedding=None,
            max_distance=MAX_DISTANCE,
            limit=50,
        )
        meaning_page = await repository.search_reminders(
            user_id=user_id,
            terms=[],
            query_embedding=_axis_vector(axis=2),
            max_distance=MAX_DISTANCE,
            limit=50,
        )
        embedding = await repository.get_embedding(user_id=user_id, reminder_id=live.id)

    assert [match.reminder.id for match in word_page.matches] == [live.id]
    assert word_page.total == 1
    assert [match.reminder.id for match in meaning_page.matches] == [live.id]
    assert embedding is not None


async def test_memory_search_matches_by_word_and_meaning(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    user_id, _ = two_users
    async with session_factory() as session:
        repository = SqlMemoryRepository(session)
        by_word = await repository.create_memory(
            user_id=user_id,
            write=MemoryWrite(
                text="My passport expires in 2030",
                category=None,
                embedding=_axis_vector(axis=3),
                origin="command",
                original_input=None,
            ),
        )
        by_meaning = await repository.create_memory(
            user_id=user_id,
            write=MemoryWrite(
                text="Career goal: become a backend engineer",
                category=None,
                embedding=_axis_vector(axis=4),
                origin="command",
                original_input=None,
            ),
        )
        page = await repository.search_memories(
            user_id=user_id,
            terms=["passport"],
            query_embedding=_axis_vector(axis=4),
            max_distance=MAX_DISTANCE,
            limit=50,
        )

    ids = [match.memory.id for match in page.matches]
    # The word match orders first in the database's own cut.
    assert ids == [by_word.id, by_meaning.id]
    assert page.total == 2


async def test_no_terms_and_no_vector_matches_nothing(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    user_id, _ = two_users
    async with session_factory() as session:
        repository = SqlTaskRepository(session)
        await repository.create_task(
            user_id=user_id,
            title="Anything",
            due_at=None,
            origin="command",
            original_input=None,
        )
        page = await repository.search_tasks(
            user_id=user_id,
            terms=[],
            query_embedding=None,
            max_distance=MAX_DISTANCE,
            limit=50,
        )

    assert page.matches == []
    assert page.total == 0
