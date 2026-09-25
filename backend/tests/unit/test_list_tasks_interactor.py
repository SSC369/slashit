"""Listing, filtering, searching and sorting tasks.

FR-15, FR-16, FR-17, FR-25, FR-43.
"""

import uuid
from datetime import UTC, datetime, timedelta

from app.domains.records.interactors.dtos import ListTasksInputDTO
from app.domains.records.interactors.list_tasks import ListTasksInteractor
from app.domains.records.interfaces.dtos import TaskDTO
from tests.fakes.fake_memory_port import FakeMemoryRecordsPort
from tests.fakes.fake_reminder_records_port import FakeReminderRecordsPort
from tests.fakes.fake_task_repository import FakeTaskRepository


async def _seeded_repository(*, user_id: uuid.UUID) -> FakeTaskRepository:
    repository = FakeTaskRepository()
    await repository.create_task(
        user_id=user_id,
        title="Finish API docs",
        due_at=None,
        origin="command",
        original_input="/add-task Finish API docs",
    )
    await repository.create_task(
        user_id=user_id,
        title="Renew insurance",
        due_at=None,
        origin="command",
        original_input="/add-task Renew insurance",
    )
    return repository


async def test_kind_filter_tasks_returns_every_row() -> None:
    """T-2.1. Every row is already a task in this epic."""
    user_id = uuid.uuid4()
    repository = await _seeded_repository(user_id=user_id)
    interactor = ListTasksInteractor(
        memory_records=FakeMemoryRecordsPort(),
        task_repository=repository,
        reminder_records=FakeReminderRecordsPort(),
    )

    tasks = await interactor.list_tasks(
        dto=ListTasksInputDTO(
            user_id=user_id,
            kind_filter="TASKS",
            search=None,
            sort_by="CREATED_AT",
            sort_desc=False,
        )
    )

    assert len(tasks) == 2


async def test_search_matches_title_case_insensitively() -> None:
    """T-2.2."""
    user_id = uuid.uuid4()
    repository = await _seeded_repository(user_id=user_id)
    interactor = ListTasksInteractor(
        memory_records=FakeMemoryRecordsPort(),
        task_repository=repository,
        reminder_records=FakeReminderRecordsPort(),
    )

    tasks = await interactor.list_tasks(
        dto=ListTasksInputDTO(
            user_id=user_id,
            kind_filter=None,
            search="docs",
            sort_by="CREATED_AT",
            sort_desc=False,
        )
    )

    assert [task.title for task in tasks if isinstance(task, TaskDTO)] == [
        "Finish API docs"
    ]


async def test_sorting_by_due_at_puts_null_last_ascending() -> None:
    """T-2.3."""
    user_id = uuid.uuid4()
    repository = FakeTaskRepository()
    now = datetime.now(UTC)
    await repository.create_task(
        user_id=user_id,
        title="No due date",
        due_at=None,
        origin="command",
        original_input=None,
    )
    await repository.create_task(
        user_id=user_id,
        title="Due tomorrow",
        due_at=now + timedelta(days=1),
        origin="command",
        original_input=None,
    )
    interactor = ListTasksInteractor(
        memory_records=FakeMemoryRecordsPort(),
        task_repository=repository,
        reminder_records=FakeReminderRecordsPort(),
    )

    tasks = await interactor.list_tasks(
        dto=ListTasksInputDTO(
            user_id=user_id,
            kind_filter=None,
            search=None,
            sort_by="DUE_AT",
            sort_desc=False,
        )
    )

    assert [task.title for task in tasks if isinstance(task, TaskDTO)] == [
        "Due tomorrow",
        "No due date",
    ]


async def test_overdue_pending_task_reports_overdue_and_done_does_not() -> None:
    """T-2.4."""
    user_id = uuid.uuid4()
    repository = FakeTaskRepository()
    past = datetime.now(UTC) - timedelta(days=1)
    overdue = await repository.create_task(
        user_id=user_id,
        title="Overdue",
        due_at=past,
        origin="command",
        original_input=None,
    )
    assert overdue.is_overdue is True

    done = await repository.set_status(
        user_id=user_id, task_id=overdue.id, status="done"
    )
    assert done is not None
    assert done.is_overdue is False
