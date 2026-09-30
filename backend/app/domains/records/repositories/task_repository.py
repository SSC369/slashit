"""The only SQL in the records domain. Returns DTOs, never models."""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import CursorResult, case, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import user_transaction
from app.core.text_search import build_search_expressions
from app.domains.records.interfaces.dtos import (
    RecordOrigin,
    TaskDTO,
    TaskEmbeddingTargetDTO,
    TaskSearchMatchDTO,
    TaskSearchPageDTO,
    TaskStatus,
)
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
            # A changed title's old vector describes the old words. NULL until
            # the embed job runs, so an old meaning never matches (005 FR-14).
            # An unchanged title keeps its vector.
            values["embedding"] = case(
                (Task.title == title, Task.embedding), else_=None
            )
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

    async def search_tasks(
        self,
        *,
        user_id: uuid.UUID,
        terms: Sequence[str],
        query_embedding: Sequence[float] | None,
        max_distance: float,
        limit: int,
    ) -> TaskSearchPageDTO:
        """Live tasks matching any term or within ``max_distance`` (005 §5).

        Ordered for the database's own cut at ``limit`` only; search ranks.
        """
        expressions = build_search_expressions(
            search_vector=Task.search_vector,
            embedding=Task.embedding,
            terms=terms,
            query_embedding=query_embedding,
            max_distance=max_distance,
        )
        if expressions.matches is None:
            return TaskSearchPageDTO(matches=[], total=0)
        live_matches = (
            Task.user_id == user_id,
            Task.deleted_at.is_(None),
            expressions.matches,
        )
        statement = (
            select(
                Task,
                expressions.all_terms,
                expressions.word_rank,
                expressions.distance,
            )
            .where(*live_matches)
            .order_by(*expressions.ordering)
            .limit(limit)
        )
        now = datetime.now(UTC)
        async with user_transaction(self.session, user_id) as scoped:
            rows = (await scoped.execute(statement)).all()
            total = await scoped.scalar(
                select(func.count()).select_from(Task).where(*live_matches)
            )
        return TaskSearchPageDTO(
            matches=[
                TaskSearchMatchDTO(
                    task=_task_to_dto(task=task, now=now),
                    all_terms=bool(all_terms),
                    word_rank=word_rank,
                    distance=distance,
                )
                for task, all_terms, word_rank, distance in rows
            ],
            total=int(total or 0),
        )

    async def get_embedding(
        self, *, user_id: uuid.UUID, task_id: uuid.UUID
    ) -> tuple[float, ...] | None:
        async with user_transaction(self.session, user_id) as scoped:
            embedding = await scoped.scalar(
                select(Task.embedding).where(
                    Task.id == task_id,
                    Task.user_id == user_id,
                    Task.deleted_at.is_(None),
                )
            )
        return None if embedding is None else tuple(float(item) for item in embedding)

    async def get_title_needing_embedding(
        self, *, user_id: uuid.UUID, task_id: uuid.UUID
    ) -> str | None:
        """The live task's title while it has no vector, else None: gone, or
        already embedded, as after an edit that left the title unchanged."""
        async with user_transaction(self.session, user_id) as scoped:
            title = await scoped.scalar(
                select(Task.title).where(
                    Task.id == task_id,
                    Task.user_id == user_id,
                    Task.deleted_at.is_(None),
                    Task.embedding.is_(None),
                )
            )
        return None if title is None else str(title)

    async def set_embedding(
        self,
        *,
        user_id: uuid.UUID,
        task_id: uuid.UUID,
        title: str,
        embedding: Sequence[float],
    ) -> bool:
        """Store the vector only if the title is still the one embedded, so a
        vector computed before a later edit is never written over it."""
        async with user_transaction(self.session, user_id) as scoped:
            result = cast(
                CursorResult[Any],
                await scoped.execute(
                    update(Task)
                    .where(
                        Task.id == task_id,
                        Task.user_id == user_id,
                        Task.deleted_at.is_(None),
                        Task.title == title,
                    )
                    .values(embedding=list(embedding))
                ),
            )
        return result.rowcount > 0

    async def select_missing_embeddings(
        self,
        *,
        updated_since: datetime | None,
        after_id: uuid.UUID | None,
        limit: int,
    ) -> list[TaskEmbeddingTargetDTO]:
        """Every user's live tasks with no vector. Cross-user by design: the
        backfill job runs on the service-role connection (T3), never a request.
        ``updated_since`` None means every such task, for the full sweep."""
        statement = select(Task.user_id, Task.id).where(
            Task.embedding.is_(None), Task.deleted_at.is_(None)
        )
        if updated_since is not None:
            statement = statement.where(Task.updated_at >= updated_since)
        if after_id is not None:
            statement = statement.where(Task.id > after_id)
        # No user_transaction: the sweep reads every user's rows on the
        # service-role connection, as a background job may (T3).
        async with self.session.begin():
            rows = (
                await self.session.execute(statement.order_by(Task.id).limit(limit))
            ).all()
        return [
            TaskEmbeddingTargetDTO(user_id=user_id, task_id=task_id)
            for user_id, task_id in rows
        ]
