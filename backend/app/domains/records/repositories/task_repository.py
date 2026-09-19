"""The only SQL in the records domain. Returns DTOs, never models."""

import uuid
from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import CursorResult, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import user_transaction
from app.domains.records.interfaces.dtos import RecordOrigin, TaskDTO, TaskStatus
from app.domains.records.models import Task


def _task_to_dto(*, task: Task, now: datetime) -> TaskDTO:
    return TaskDTO(
        id=task.id,
        user_id=task.user_id,
        title=task.title,
        due_at=task.due_at,
        status=cast(TaskStatus, task.status),
        is_overdue=(
            task.due_at is not None and task.due_at < now and task.status == "pending"
        ),
        origin=cast(RecordOrigin, task.origin),
        original_input=task.original_input,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


class SqlTaskRepository:
    """Reads and writes ``tasks``, against the request's own session.

    Unlike the gateway's usage repository, nothing here needs a write to
    survive the caller's later work rolling back (there is no AD-8-equivalent
    requirement), so this uses the request's single session directly, per the
    canonical pattern in backend/.claude/rules/repo-rules.md section 7.4.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

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
        task_id = uuid.uuid4()
        async with user_transaction(self.session, user_id) as scoped:
            scoped.add(
                Task(
                    id=task_id,
                    user_id=user_id,
                    title=title,
                    due_at=due_at,
                    status="pending",
                    origin=origin,
                    original_input=original_input,
                    created_at=now,
                    updated_at=now,
                )
            )
        return TaskDTO(
            id=task_id,
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

    async def list_open_tasks_for_user(self, *, user_id: uuid.UUID) -> list[TaskDTO]:
        now = datetime.now(UTC)
        async with user_transaction(self.session, user_id) as scoped:
            result = await scoped.scalars(
                select(Task)
                .where(
                    Task.user_id == user_id,
                    Task.status == "pending",
                    Task.deleted_at.is_(None),
                )
                .order_by(Task.due_at.is_(None), Task.due_at.asc())
            )
            tasks = result.all()
        return [_task_to_dto(task=task, now=now) for task in tasks]

    async def list_for_user(
        self,
        *,
        user_id: uuid.UUID,
        kind_filter: str | None,
        search: str | None,
        sort_by: str,
        sort_desc: bool,
    ) -> list[TaskDTO]:
        # kind_filter has one legal non-null value ("TASKS") and every row in
        # this table already is a task, so it never excludes a row today. It
        # stays a real parameter because a second record type will make it do
        # something without a signature change.
        now = datetime.now(UTC)
        statement = select(Task).where(
            Task.user_id == user_id, Task.deleted_at.is_(None)
        )
        if search:
            statement = statement.where(Task.title.ilike(f"%{search}%"))

        sort_column = Task.due_at if sort_by == "DUE_AT" else Task.created_at
        direction = sort_column.desc() if sort_desc else sort_column.asc()
        statement = statement.order_by(sort_column.is_(None), direction)

        async with user_transaction(self.session, user_id) as scoped:
            result = await scoped.scalars(statement)
            tasks = result.all()
        return [_task_to_dto(task=task, now=now) for task in tasks]

    async def get_by_id(
        self, *, user_id: uuid.UUID, task_id: uuid.UUID
    ) -> TaskDTO | None:
        now = datetime.now(UTC)
        async with user_transaction(self.session, user_id) as scoped:
            task = await scoped.get(Task, task_id)
        if task is None or task.user_id != user_id or task.deleted_at is not None:
            return None
        return _task_to_dto(task=task, now=now)

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
        now = datetime.now(UTC)
        values: dict[str, object] = {"updated_at": now}
        if title is not None:
            values["title"] = title
        if status is not None:
            values["status"] = status
        if due_at_provided:
            values["due_at"] = due_at

        async with user_transaction(self.session, user_id) as scoped:
            await scoped.execute(
                update(Task)
                .where(
                    Task.id == task_id,
                    Task.user_id == user_id,
                    Task.deleted_at.is_(None),
                )
                .values(**values)
            )
            task = await scoped.get(Task, task_id)
        if task is None or task.user_id != user_id or task.deleted_at is not None:
            return None
        return _task_to_dto(task=task, now=now)

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
        """Soft-delete: sets ``deleted_at`` rather than removing the row.

        User decision 2026-09-19: no task is ever hard-deleted. Every read
        path filters ``deleted_at IS NULL``, so a soft-deleted task behaves,
        from every other method's point of view, as if it were gone.
        """
        async with user_transaction(self.session, user_id) as scoped:
            result = cast(
                CursorResult[Any],
                await scoped.execute(
                    update(Task)
                    .where(
                        Task.user_id == user_id,
                        Task.id.in_(task_ids),
                        Task.deleted_at.is_(None),
                    )
                    .values(deleted_at=datetime.now(UTC))
                ),
            )
        return result.rowcount
