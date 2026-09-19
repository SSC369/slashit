"""Deleting one or many tasks. FR-20, FR-21."""

import uuid

from app.domains.records.interactors.delete_tasks import DeleteTasksInteractor
from app.domains.records.interactors.dtos import DeleteTasksInputDTO
from tests.fakes.fake_task_repository import FakeTaskRepository


async def test_deleting_two_ids_removes_both_and_returns_count_two() -> None:
    """T-2.8."""
    user_id = uuid.uuid4()
    repository = FakeTaskRepository()
    first = await repository.create_task(
        user_id=user_id,
        title="First",
        due_at=None,
        origin="command",
        original_input=None,
    )
    second = await repository.create_task(
        user_id=user_id,
        title="Second",
        due_at=None,
        origin="command",
        original_input=None,
    )

    interactor = DeleteTasksInteractor(task_repository=repository)
    deleted_count = await interactor.delete_tasks(
        dto=DeleteTasksInputDTO(user_id=user_id, task_ids=[first.id, second.id])
    )

    assert deleted_count == 2
    assert await repository.get_by_id(user_id=user_id, task_id=first.id) is None
    assert await repository.get_by_id(user_id=user_id, task_id=second.id) is None


async def test_deleting_an_already_deleted_id_counts_as_zero() -> None:
    """Soft delete, user decision 2026-09-19: a second delete of the same id
    is a no-op, not a second write."""
    user_id = uuid.uuid4()
    repository = FakeTaskRepository()
    task = await repository.create_task(
        user_id=user_id,
        title="Once",
        due_at=None,
        origin="command",
        original_input=None,
    )
    interactor = DeleteTasksInteractor(task_repository=repository)

    first = await interactor.delete_tasks(
        dto=DeleteTasksInputDTO(user_id=user_id, task_ids=[task.id])
    )
    second = await interactor.delete_tasks(
        dto=DeleteTasksInputDTO(user_id=user_id, task_ids=[task.id])
    )

    assert first == 1
    assert second == 0


async def test_ids_not_owned_are_ignored_not_deleted() -> None:
    owner_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    repository = FakeTaskRepository()
    task = await repository.create_task(
        user_id=owner_id,
        title="Not yours",
        due_at=None,
        origin="command",
        original_input=None,
    )

    interactor = DeleteTasksInteractor(task_repository=repository)
    deleted_count = await interactor.delete_tasks(
        dto=DeleteTasksInputDTO(user_id=other_user_id, task_ids=[task.id])
    )

    assert deleted_count == 0
    assert await repository.get_by_id(user_id=owner_id, task_id=task.id) is not None
