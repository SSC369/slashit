"""004 P-6: a save survives an unreachable job queue, and a sweep queues the
vector it missed."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from procrastinate.exceptions import ConnectorException

from app.core.jobs import procrastinate_app
from app.domains.memories.interactors.queue_missing_embeddings import (
    QueueMissingEmbeddingsInteractor,
)
from app.domains.memories.interfaces.repositories import MemoryWrite
from app.domains.memories.services.reembed_queue import ProcrastinateReembedQueue
from tests.fakes.fake_memory_repository import FakeMemoryRepository, FakeReembedQueue


class _UnreachableQueue:
    def __init__(self, **_: Any) -> None:
        self.deferred = False

    async def defer_async(self, **_: Any) -> None:
        self.deferred = True
        raise ConnectorException()


def _write(*, text: str, embedding: tuple[float, ...] | None) -> MemoryWrite:
    return MemoryWrite(
        text=text,
        category=None,
        embedding=embedding,
        origin="command",
        original_input=None,
    )


async def test_an_unreachable_queue_does_not_fail_the_committed_save(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """P-6: the answer used to report "Nothing changed" after the memory had
    committed, and a retry saved it twice."""
    queue = _UnreachableQueue()
    monkeypatch.setattr(procrastinate_app, "configure_task", lambda **_: queue)

    await ProcrastinateReembedQueue().enqueue_reembed(
        user_id=uuid.uuid4(), memory_id=uuid.uuid4()
    )

    assert queue.deferred


async def test_the_sweep_queues_only_recent_memories_with_no_vector() -> None:
    """P-6: the backfill picks up what the unreachable queue missed."""
    repository = FakeMemoryRepository()
    user_id = uuid.uuid4()
    missing = await repository.create_memory(
        user_id=user_id, write=_write(text="Gym is Cult Fit", embedding=None)
    )
    await repository.create_memory(
        user_id=user_id, write=_write(text="Car is a Swift", embedding=(0.1,) * 768)
    )
    queue = FakeReembedQueue()
    interactor = QueueMissingEmbeddingsInteractor(
        memory_repository=repository,
        reembed_queue=queue,
        now_provider=lambda: datetime.now(UTC),
    )

    assert await interactor.queue_missing_embeddings() == 1
    assert queue.queued == [missing.id]

    later = QueueMissingEmbeddingsInteractor(
        memory_repository=repository,
        reembed_queue=FakeReembedQueue(),
        now_provider=lambda: datetime.now(UTC) + timedelta(days=2),
    )
    assert await later.queue_missing_embeddings() == 0
