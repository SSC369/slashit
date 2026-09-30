"""The contract for records storage.

Slice 1 (04.1-capture-core.md) needed only creation and the open-tasks list
`/tasks` reads. Slice 2 (04.2-records-and-settings.md) extends this same
Protocol with list, detail, update, set-status and delete, rather than
creating a second one.
"""

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domains.records.interfaces.dtos import (
    RecordOrigin,
    TaskDTO,
    TaskEmbeddingTargetDTO,
    TaskSearchPageDTO,
    TaskStatus,
)


class TaskRepository(Protocol):
    async def create_task(
        self,
        *,
        user_id: UUID,
        title: str,
        due_at: datetime | None,
        origin: RecordOrigin,
        original_input: str | None,
    ) -> TaskDTO: ...

    async def list_open_tasks_for_user(self, *, user_id: UUID) -> list[TaskDTO]: ...

    async def list_for_user(
        self,
        *,
        user_id: UUID,
        kind_filter: str | None,
        sort_by: str,
        sort_desc: bool,
    ) -> list[TaskDTO]: ...

    async def get_by_id(self, *, user_id: UUID, task_id: UUID) -> TaskDTO | None: ...

    async def update(
        self,
        *,
        user_id: UUID,
        task_id: UUID,
        title: str | None,
        status: TaskStatus | None,
        due_at: datetime | None,
        due_at_provided: bool,
    ) -> TaskDTO | None: ...

    async def set_status(
        self, *, user_id: UUID, task_id: UUID, status: TaskStatus
    ) -> TaskDTO | None: ...

    async def delete_many(self, *, user_id: UUID, task_ids: list[UUID]) -> int: ...

    # Epic 005, sub-plan 4.1.
    async def search_tasks(
        self,
        *,
        user_id: UUID,
        terms: Sequence[str],
        query_embedding: Sequence[float] | None,
        max_distance: float,
        limit: int,
    ) -> TaskSearchPageDTO: ...

    async def get_embedding(
        self, *, user_id: UUID, task_id: UUID
    ) -> tuple[float, ...] | None: ...

    async def get_title_needing_embedding(
        self, *, user_id: UUID, task_id: UUID
    ) -> str | None: ...

    async def set_embedding(
        self, *, user_id: UUID, task_id: UUID, title: str, embedding: Sequence[float]
    ) -> bool: ...

    async def select_missing_embeddings(
        self,
        *,
        updated_since: datetime | None,
        after_id: UUID | None,
        limit: int,
    ) -> list[TaskEmbeddingTargetDTO]:
        """Live rows of every user with no vector, in id order after
        ``after_id``. For the backfill job only: reads across users."""
        ...
