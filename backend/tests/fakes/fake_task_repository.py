"""An in-memory TaskRepository. Not a mock: it behaves, so tests read as
behaviour."""

import uuid
from datetime import UTC, datetime

from app.domains.records.interfaces.dtos import RecordOrigin, TaskDTO, TaskStatus


class FakeTaskRepository:
    """Satisfies records' TaskRepository Protocol without inheriting from it."""

    def __init__(self) -> None:
        self.tasks: dict[uuid.UUID, TaskDTO] = {}
        self.deleted_ids: set[uuid.UUID] = set()

    async def create_task(
        self,
        *,
        user_id: uuid.UUID,
        title: str,
        due_at: datetime | None,
        origin: RecordOrigin,
        original_input: str | None,
    ) -> TaskDTO:
        now = datetime.now(UTC)
        task = TaskDTO(
            id=uuid.uuid4(),
            user_id=user_id,
            title=title,
            due_at=due_at,
            status="pending",
            is_overdue=due_at is not None and due_at < now,
            origin=origin,
            original_input=original_input,
            created_at=now,
            updated_at=now,
        )
        self.tasks[task.id] = task
        return task

    async def list_open_tasks_for_user(self, *, user_id: uuid.UUID) -> list[TaskDTO]:
        return [
            task
            for task in self.tasks.values()
            if task.user_id == user_id
            and task.status == "pending"
            and task.id not in self.deleted_ids
        ]

    async def list_for_user(
        self,
        *,
        user_id: uuid.UUID,
        kind_filter: str | None,
        search: str | None,
        sort_by: str,
        sort_desc: bool,
    ) -> list[TaskDTO]:
        tasks = [
            task
            for task in self.tasks.values()
            if task.user_id == user_id and task.id not in self.deleted_ids
        ]
        if search:
            tasks = [task for task in tasks if search.lower() in task.title.lower()]

        def sort_key(task: TaskDTO) -> tuple[bool, datetime]:
            value = task.due_at if sort_by == "DUE_AT" else task.created_at
            return (value is None, value or datetime.min.replace(tzinfo=UTC))

        tasks.sort(key=sort_key, reverse=sort_desc)
        return tasks

    async def get_by_id(
        self, *, user_id: uuid.UUID, task_id: uuid.UUID
    ) -> TaskDTO | None:
        task = self.tasks.get(task_id)
        if task is None or task.user_id != user_id or task_id in self.deleted_ids:
            return None
        return task

    async def update(
        self,
        *,
        user_id: uuid.UUID,
        task_id: uuid.UUID,
        title: str | None,
        status: TaskStatus | None,
        due_at: datetime | None,
        due_at_provided: bool,
    ) -> TaskDTO | None:
        task = self.tasks.get(task_id)
        if task is None or task.user_id != user_id or task_id in self.deleted_ids:
            return None
        now = datetime.now(UTC)
        new_due_at = due_at if due_at_provided else task.due_at
        updated = TaskDTO(
            id=task.id,
            user_id=task.user_id,
            title=title if title is not None else task.title,
            due_at=new_due_at,
            status=status if status is not None else task.status,
            is_overdue=new_due_at is not None
            and new_due_at < now
            and (status or task.status) == "pending",
            origin=task.origin,
            original_input=task.original_input,
            created_at=task.created_at,
            updated_at=now,
        )
        self.tasks[task_id] = updated
        return updated

    async def set_status(
        self, *, user_id: uuid.UUID, task_id: uuid.UUID, status: TaskStatus
    ) -> TaskDTO | None:
        return await self.update(
            user_id=user_id,
            task_id=task_id,
            title=None,
            status=status,
            due_at=None,
            due_at_provided=False,
        )

    async def delete_many(
        self, *, user_id: uuid.UUID, task_ids: list[uuid.UUID]
    ) -> int:
        """Soft delete, same as SqlTaskRepository: rows stay in ``self.tasks``,
        marked in ``self.deleted_ids``, so a test can still assert on what a
        deleted task looked like if it needs to."""
        deleted = 0
        for task_id in task_ids:
            task = self.tasks.get(task_id)
            if (
                task is not None
                and task.user_id == user_id
                and task_id not in self.deleted_ids
            ):
                self.deleted_ids.add(task_id)
                deleted += 1
        return deleted
