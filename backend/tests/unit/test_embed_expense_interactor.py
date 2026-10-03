"""Epic 006, sub-plan 4.3 §7: C-37 and C-38. The embed job and its backfill."""

import uuid
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta

import pytest

from app.domains.expenses.interactors.dtos import (
    EmbedExpenseInputDTO,
    QueueMissingExpenseEmbeddingsInputDTO,
)
from app.domains.expenses.interactors.embed_expense import (
    EmbedExpenseFailedError,
    EmbedExpenseInteractor,
)
from app.domains.expenses.interactors.queue_missing_expense_embeddings import (
    QueueMissingExpenseEmbeddingsInteractor,
)
from app.domains.expenses.interfaces.dtos import ExpenseCategory, ExpenseChanges
from app.domains.expenses.interfaces.repositories import ExpenseWrite
from tests.fakes.fake_expense_embed_queue import FakeExpenseEmbedQueue
from tests.fakes.fake_expense_repository import FakeExpenseRepository

USER = uuid.uuid4()
VECTOR = (0.1, 0.2, 0.3)


class _Embedder:
    def __init__(self, *, vector: tuple[float, ...] | None) -> None:
        self.vector = vector
        self.described: list[str] = []

    async def embed_expense_description(
        self, *, user_id: uuid.UUID, description: str
    ) -> tuple[float, ...] | None:
        self.described.append(description)
        return self.vector


async def _saved(repository: FakeExpenseRepository, description: str) -> uuid.UUID:
    expense = await repository.create_expense(
        user_id=USER,
        write=ExpenseWrite(
            amount_paise=85_000,
            description=description,
            category=ExpenseCategory.FOOD,
            spent_on=date(2026, 10, 2),
            origin="command",
            original_input=f"/add-expense 850 {description}",
        ),
    )
    return expense.id


async def test_the_description_is_embedded_and_stored() -> None:
    repository = FakeExpenseRepository()
    expense_id = await _saved(repository, "dinner at Toit")
    embedder = _Embedder(vector=VECTOR)

    embedded = await EmbedExpenseInteractor(
        expense_repository=repository, embedding=embedder
    ).embed_expense(dto=EmbedExpenseInputDTO(user_id=USER, expense_id=expense_id))

    assert embedded is True
    assert embedder.described == ["dinner at Toit"]
    assert repository.embeddings[expense_id] == VECTOR


async def test_a_deleted_or_already_embedded_expense_is_skipped() -> None:
    repository = FakeExpenseRepository()
    deleted_id = await _saved(repository, "lunch")
    await repository.soft_delete(user_id=USER, expense_id=deleted_id)
    embedded_id = await _saved(repository, "chai")
    repository.embeddings[embedded_id] = VECTOR
    embedder = _Embedder(vector=VECTOR)
    interactor = EmbedExpenseInteractor(
        expense_repository=repository, embedding=embedder
    )

    for expense_id in (deleted_id, embedded_id):
        assert not await interactor.embed_expense(
            dto=EmbedExpenseInputDTO(user_id=USER, expense_id=expense_id)
        )
    assert embedder.described == []


async def test_a_vector_for_old_words_is_never_written_after_an_edit() -> None:
    repository = FakeExpenseRepository()
    expense_id = await _saved(repository, "dinner")

    class _EditWhileEmbedding(_Embedder):
        async def embed_expense_description(
            self, *, user_id: uuid.UUID, description: str
        ) -> tuple[float, ...] | None:
            await repository.update_expense(
                user_id=USER,
                expense_id=expense_id,
                changes=ExpenseChanges(
                    amount_paise=None,
                    description="dinner at Toit",
                    category=None,
                    spent_on=None,
                ),
            )
            return VECTOR

    embedded = await EmbedExpenseInteractor(
        expense_repository=repository, embedding=_EditWhileEmbedding(vector=VECTOR)
    ).embed_expense(dto=EmbedExpenseInputDTO(user_id=USER, expense_id=expense_id))

    assert embedded is False
    assert expense_id not in repository.embeddings


async def test_a_model_failure_raises_so_the_job_retries() -> None:
    repository = FakeExpenseRepository()
    expense_id = await _saved(repository, "dinner")

    with pytest.raises(EmbedExpenseFailedError):
        await EmbedExpenseInteractor(
            expense_repository=repository, embedding=_Embedder(vector=None)
        ).embed_expense(dto=EmbedExpenseInputDTO(user_id=USER, expense_id=expense_id))


async def test_the_backfill_queues_recent_missing_vectors_and_full_queues_all() -> None:
    """C-38: the periodic sweep covers the window; ``full`` every one, spaced."""
    repository = FakeExpenseRepository()
    recent_id = await _saved(repository, "recent")
    old_id = await _saved(repository, "old")
    repository.rows[old_id] = replace(
        repository.rows[old_id], updated_at=datetime.now(UTC) - timedelta(days=3)
    )
    embedded_id = await _saved(repository, "done")
    repository.embeddings[embedded_id] = VECTOR

    def _queue() -> tuple[
        QueueMissingExpenseEmbeddingsInteractor, FakeExpenseEmbedQueue
    ]:
        queue = FakeExpenseEmbedQueue()
        return (
            QueueMissingExpenseEmbeddingsInteractor(
                expense_repository=repository,
                embed_queue=queue,
                now_provider=lambda: datetime.now(UTC),
            ),
            queue,
        )

    periodic, periodic_queue = _queue()
    full, full_queue = _queue()

    assert (
        await periodic.queue_missing_expense_embeddings(
            dto=QueueMissingExpenseEmbeddingsInputDTO(full=False)
        )
        == 1
    )
    assert [queued[1] for queued in periodic_queue.queued] == [recent_id]
    assert (
        await full.queue_missing_expense_embeddings(
            dto=QueueMissingExpenseEmbeddingsInputDTO(full=True)
        )
        == 2
    )
    assert {queued[1] for queued in full_queue.queued} == {recent_id, old_id}
