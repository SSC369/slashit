"""Epic 005, sub-plan 4.1, C-10: the embed backfill against a real database.

The full sweep, run once at deploy, queues every live task and reminder with
no vector however old, and spaces the jobs (FR-13, index §6). The periodic
sweep only sees rows touched in the last 24 hours.
"""

import uuid
from datetime import UTC, date, datetime, time, timedelta

import pytest
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.records.constants import BACKFILL_CALLS_PER_SECOND
from app.domains.records.interactors import queue_missing_task_embeddings
from app.domains.records.interactors.dtos import QueueMissingTaskEmbeddingsInputDTO
from app.domains.records.interactors.queue_missing_task_embeddings import (
    QueueMissingTaskEmbeddingsInteractor,
)
from app.domains.records.models import Task
from app.domains.records.repositories.task_repository import SqlTaskRepository
from app.domains.reminders.interactors.dtos import (
    QueueMissingReminderEmbeddingsInputDTO,
)
from app.domains.reminders.interactors.queue_missing_reminder_embeddings import (
    QueueMissingReminderEmbeddingsInteractor,
)
from app.domains.reminders.interfaces.repositories import ReminderWrite
from app.domains.reminders.repositories.reminder_repository import (
    SqlReminderRepository,
)
from app.domains.reminders.services.schedule import RepeatKind, ScheduleSpec
from tests.fakes.fake_embed_queues import FakeReminderEmbedQueue, FakeTaskEmbedQueue


def _now() -> datetime:
    return datetime.now(UTC)


async def _create_tasks(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    user_id: uuid.UUID,
    count: int,
) -> list[uuid.UUID]:
    async with session_factory() as session:
        repository = SqlTaskRepository(session)
        task_ids = []
        for index in range(count):
            task = await repository.create_task(
                user_id=user_id,
                title=f"Backfill task {index}",
                due_at=None,
                origin="command",
                original_input=None,
            )
            task_ids.append(task.id)
    return task_ids


async def _age_task(
    *, session_factory: async_sessionmaker[AsyncSession], task_id: uuid.UUID
) -> None:
    """Move a task's last change outside the periodic sweep's window."""
    async with session_factory() as session, session.begin():
        await session.execute(
            update(Task)
            .where(Task.id == task_id)
            .values(updated_at=datetime.now(UTC) - timedelta(days=30))
        )


async def test_the_full_sweep_queues_old_tasks_and_the_periodic_one_does_not(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    user_id, _ = two_users
    old_id, recent_id = await _create_tasks(
        session_factory=session_factory, user_id=user_id, count=2
    )
    await _age_task(session_factory=session_factory, task_id=old_id)

    periodic_queue, full_queue = FakeTaskEmbedQueue(), FakeTaskEmbedQueue()
    async with session_factory() as session:
        await QueueMissingTaskEmbeddingsInteractor(
            task_repository=SqlTaskRepository(session),
            embed_queue=periodic_queue,
            now_provider=_now,
        ).queue_missing_task_embeddings(
            dto=QueueMissingTaskEmbeddingsInputDTO(full=False)
        )
    async with session_factory() as session:
        await QueueMissingTaskEmbeddingsInteractor(
            task_repository=SqlTaskRepository(session),
            embed_queue=full_queue,
            now_provider=_now,
        ).queue_missing_task_embeddings(
            dto=QueueMissingTaskEmbeddingsInputDTO(full=True)
        )

    periodic_ids = {task_id for _, task_id, _ in periodic_queue.queued}
    full_ids = {task_id for _, task_id, _ in full_queue.queued}
    assert recent_id in periodic_ids
    assert old_id not in periodic_ids
    assert {old_id, recent_id} <= full_ids


async def test_the_full_sweep_walks_every_page_and_spaces_the_jobs(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """More tasks than one batch: every one is queued, a few per second."""
    user_id, _ = two_users
    monkeypatch.setattr(queue_missing_task_embeddings, "EMBEDDING_BACKFILL_BATCH", 3)
    created = await _create_tasks(
        session_factory=session_factory, user_id=user_id, count=7
    )
    queue = FakeTaskEmbedQueue()
    async with session_factory() as session:
        queued_count = await QueueMissingTaskEmbeddingsInteractor(
            task_repository=SqlTaskRepository(session),
            embed_queue=queue,
            now_provider=_now,
        ).queue_missing_task_embeddings(
            dto=QueueMissingTaskEmbeddingsInputDTO(full=True)
        )

    mine = [entry for entry in queue.queued if entry[1] in set(created)]
    assert {task_id for _, task_id, _ in mine} == set(created)
    assert queued_count >= len(created)
    delays = [delay for _, _, delay in queue.queued]
    assert delays == sorted(delays)
    assert delays[-1] == (len(queue.queued) - 1) // BACKFILL_CALLS_PER_SECOND


async def test_the_full_sweep_skips_embedded_and_deleted_tasks(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    user_id, _ = two_users
    embedded_id, deleted_id, missing_id = await _create_tasks(
        session_factory=session_factory, user_id=user_id, count=3
    )
    async with session_factory() as session:
        repository = SqlTaskRepository(session)
        await repository.set_embedding(
            user_id=user_id,
            task_id=embedded_id,
            title="Backfill task 0",
            embedding=(0.1,) * 768,
        )
        await repository.delete_many(user_id=user_id, task_ids=[deleted_id])
    queue = FakeTaskEmbedQueue()
    async with session_factory() as session:
        await QueueMissingTaskEmbeddingsInteractor(
            task_repository=SqlTaskRepository(session),
            embed_queue=queue,
            now_provider=_now,
        ).queue_missing_task_embeddings(
            dto=QueueMissingTaskEmbeddingsInputDTO(full=True)
        )

    queued_ids = {task_id for _, task_id, _ in queue.queued}
    assert missing_id in queued_ids
    assert embedded_id not in queued_ids
    assert deleted_id not in queued_ids


async def test_the_reminder_full_sweep_queues_a_reminder_with_no_vector(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    user_id, _ = two_users
    async with session_factory() as session:
        reminder = await SqlReminderRepository(session).create_reminder(
            user_id=user_id,
            write=ReminderWrite(
                description="Check passport renewal requirements",
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
            ),
            origin="command",
            original_input=None,
        )
    queue = FakeReminderEmbedQueue()
    async with session_factory() as session:
        await QueueMissingReminderEmbeddingsInteractor(
            reminder_repository=SqlReminderRepository(session),
            embed_queue=queue,
            now_provider=_now,
        ).queue_missing_reminder_embeddings(
            dto=QueueMissingReminderEmbeddingsInputDTO(full=True)
        )

    assert reminder.id in {reminder_id for _, reminder_id, _ in queue.queued}
