"""Epic 005, sub-plan 4.1, C-9: a task is queued for a vector on create and on
a title edit, never on a status-only edit, and the embed interactor stores it
(FR-14, AD-7). The reminder twin is in test_reminder_embedding.py."""

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field

import pytest

from app.domains.records.interactors.dtos import EmbedTaskInputDTO, UpdateTaskInputDTO
from app.domains.records.interactors.embed_task import (
    EmbedTaskFailedError,
    EmbedTaskInteractor,
)
from app.domains.records.interactors.update_task import UpdateTaskInteractor
from app.domains.records.services.records_service import RecordsService
from tests.fakes.fake_embed_queues import FakeTaskEmbedQueue
from tests.fakes.fake_task_repository import FakeTaskRepository


@dataclass
class _VectorStore:
    """The four embedding methods EmbedTaskInteractor needs, in memory."""

    titles: dict[uuid.UUID, str] = field(default_factory=dict)
    vectors: dict[uuid.UUID, tuple[float, ...]] = field(default_factory=dict)

    async def get_title_needing_embedding(
        self, *, user_id: uuid.UUID, task_id: uuid.UUID
    ) -> str | None:
        if task_id in self.vectors:
            return None
        return self.titles.get(task_id)

    async def set_embedding(
        self,
        *,
        user_id: uuid.UUID,
        task_id: uuid.UUID,
        title: str,
        embedding: Sequence[float],
    ) -> bool:
        if self.titles.get(task_id) != title:
            return False
        self.vectors[task_id] = tuple(embedding)
        return True


@dataclass
class _Embedder:
    vector: tuple[float, ...] | None
    calls: list[str] = field(default_factory=list)

    async def embed_task_title(
        self, *, user_id: uuid.UUID, title: str
    ) -> tuple[float, ...] | None:
        self.calls.append(title)
        return self.vector


async def test_creating_a_task_queues_one_embed() -> None:
    queue = FakeTaskEmbedQueue()
    service = RecordsService(task_repository=FakeTaskRepository(), embed_queue=queue)
    user_id = uuid.uuid4()

    task = await service.create_task(
        user_id=user_id,
        title="Renew passport",
        due_at=None,
        origin="command",
        original_input=None,
    )

    assert queue.queued == [(user_id, task.id, 0)]


async def test_a_title_edit_queues_an_embed_and_a_status_edit_does_not() -> None:
    repository = FakeTaskRepository()
    queue = FakeTaskEmbedQueue()
    user_id = uuid.uuid4()
    task = await repository.create_task(
        user_id=user_id,
        title="Renew passport",
        due_at=None,
        origin="command",
        original_input=None,
    )
    interactor = UpdateTaskInteractor(task_repository=repository, embed_queue=queue)

    await interactor.update_task(
        dto=UpdateTaskInputDTO(
            user_id=user_id,
            task_id=task.id,
            title=None,
            status="done",
            due_at=None,
            due_at_provided=False,
        )
    )
    assert queue.queued == []

    await interactor.update_task(
        dto=UpdateTaskInputDTO(
            user_id=user_id,
            task_id=task.id,
            title="Renew driving licence",
            status=None,
            due_at=None,
            due_at_provided=False,
        )
    )
    assert queue.queued == [(user_id, task.id, 0)]


async def test_the_embed_stores_a_vector_once() -> None:
    store = _VectorStore()
    task_id, user_id = uuid.uuid4(), uuid.uuid4()
    store.titles[task_id] = "Renew passport"
    embedder = _Embedder(vector=(0.5,) * 768)
    interactor = EmbedTaskInteractor(
        task_repository=store,  # type: ignore[arg-type]
        embedding=embedder,
    )
    dto = EmbedTaskInputDTO(user_id=user_id, task_id=task_id)

    first = await interactor.embed_task(dto=dto)
    second = await interactor.embed_task(dto=dto)

    assert first is True
    assert second is False
    # The second run found the vector already there and called no model.
    assert embedder.calls == ["Renew passport"]


async def test_a_refused_embed_raises_so_the_job_retries() -> None:
    store = _VectorStore()
    task_id = uuid.uuid4()
    store.titles[task_id] = "Renew passport"
    interactor = EmbedTaskInteractor(
        task_repository=store,  # type: ignore[arg-type]
        embedding=_Embedder(vector=None),
    )

    with pytest.raises(EmbedTaskFailedError):
        await interactor.embed_task(
            dto=EmbedTaskInputDTO(user_id=uuid.uuid4(), task_id=task_id)
        )
    assert store.vectors == {}


async def test_a_gone_task_is_not_embedded() -> None:
    embedder = _Embedder(vector=(0.5,) * 768)
    interactor = EmbedTaskInteractor(
        task_repository=_VectorStore(),  # type: ignore[arg-type]
        embedding=embedder,
    )

    embedded = await interactor.embed_task(
        dto=EmbedTaskInputDTO(user_id=uuid.uuid4(), task_id=uuid.uuid4())
    )

    assert embedded is False
    assert embedder.calls == []
