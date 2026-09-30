"""Editing a task's title, status and due date. FR-19, FR-22, and the error table."""

import uuid
from datetime import UTC, datetime

import pytest

from app.domains.records.graphql.errors import (
    NoFieldsToUpdateError,
    RecordNotFoundError,
)
from app.domains.records.interactors.dtos import UpdateTaskInputDTO
from app.domains.records.interactors.update_task import UpdateTaskInteractor
from tests.fakes.fake_embed_queues import FakeTaskEmbedQueue
from tests.fakes.fake_task_repository import FakeTaskRepository


async def test_updates_title_leaves_due_at_untouched_and_bumps_updated_at() -> None:
    """T-2.6."""
    user_id = uuid.uuid4()
    repository = FakeTaskRepository()
    created = await repository.create_task(
        user_id=user_id,
        title="Finish API docs",
        due_at=None,
        origin="command",
        original_input=None,
    )
    interactor = UpdateTaskInteractor(
        task_repository=repository, embed_queue=FakeTaskEmbedQueue()
    )

    updated = await interactor.update_task(
        dto=UpdateTaskInputDTO(
            user_id=user_id,
            task_id=created.id,
            title="Finish the API docs",
            status=None,
            due_at=None,
            due_at_provided=False,
        )
    )

    assert updated.title == "Finish the API docs"
    assert updated.due_at == created.due_at
    assert updated.status == "pending"
    assert updated.updated_at > created.updated_at


async def test_due_at_provided_sets_it_even_when_title_and_status_are_not() -> None:
    user_id = uuid.uuid4()
    repository = FakeTaskRepository()
    created = await repository.create_task(
        user_id=user_id,
        title="Finish API docs",
        due_at=None,
        origin="command",
        original_input=None,
    )
    interactor = UpdateTaskInteractor(
        task_repository=repository, embed_queue=FakeTaskEmbedQueue()
    )
    new_due_at = datetime(2026, 9, 20, tzinfo=UTC)

    updated = await interactor.update_task(
        dto=UpdateTaskInputDTO(
            user_id=user_id,
            task_id=created.id,
            title=None,
            status=None,
            due_at=new_due_at,
            due_at_provided=True,
        )
    )

    assert updated.due_at == new_due_at


async def test_due_at_provided_as_none_clears_an_existing_due_date() -> None:
    user_id = uuid.uuid4()
    repository = FakeTaskRepository()
    created = await repository.create_task(
        user_id=user_id,
        title="Finish API docs",
        due_at=datetime(2026, 9, 20, tzinfo=UTC),
        origin="command",
        original_input=None,
    )
    interactor = UpdateTaskInteractor(
        task_repository=repository, embed_queue=FakeTaskEmbedQueue()
    )

    updated = await interactor.update_task(
        dto=UpdateTaskInputDTO(
            user_id=user_id,
            task_id=created.id,
            title=None,
            status=None,
            due_at=None,
            due_at_provided=True,
        )
    )

    assert updated.due_at is None


async def test_no_field_provided_raises_no_fields_to_update() -> None:
    """T-2.7."""
    user_id = uuid.uuid4()
    repository = FakeTaskRepository()
    created = await repository.create_task(
        user_id=user_id,
        title="Finish API docs",
        due_at=None,
        origin="command",
        original_input=None,
    )
    interactor = UpdateTaskInteractor(
        task_repository=repository, embed_queue=FakeTaskEmbedQueue()
    )

    with pytest.raises(NoFieldsToUpdateError):
        await interactor.update_task(
            dto=UpdateTaskInputDTO(
                user_id=user_id,
                task_id=created.id,
                title=None,
                status=None,
                due_at=None,
                due_at_provided=False,
            )
        )


async def test_missing_task_raises_not_found() -> None:
    user_id = uuid.uuid4()
    repository = FakeTaskRepository()
    interactor = UpdateTaskInteractor(
        task_repository=repository, embed_queue=FakeTaskEmbedQueue()
    )

    with pytest.raises(RecordNotFoundError):
        await interactor.update_task(
            dto=UpdateTaskInputDTO(
                user_id=user_id,
                task_id=uuid.uuid4(),
                title="New title",
                status=None,
                due_at=None,
                due_at_provided=False,
            )
        )


async def test_cannot_update_another_users_task() -> None:
    owner_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    repository = FakeTaskRepository()
    created = await repository.create_task(
        user_id=owner_id,
        title="Finish API docs",
        due_at=None,
        origin="command",
        original_input=None,
    )
    interactor = UpdateTaskInteractor(
        task_repository=repository, embed_queue=FakeTaskEmbedQueue()
    )

    with pytest.raises(RecordNotFoundError):
        await interactor.update_task(
            dto=UpdateTaskInputDTO(
                user_id=other_user_id,
                task_id=created.id,
                title="Hijacked",
                status=None,
                due_at=None,
                due_at_provided=False,
            )
        )
