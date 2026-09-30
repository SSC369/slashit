"""The records domain's published surface. Extended, not replaced, by slice 2.

Per repo-rules.md section 6: a domain's whole public surface may be one class
here, re-exported from ``public.py``, for a consumer to reach through its own
port and adapter.
"""

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from app.domains.records.interfaces.dtos import (
    RecordOrigin,
    TaskDTO,
    TaskSearchPageDTO,
)
from app.domains.records.interfaces.ports import TaskEmbedQueue
from app.domains.records.interfaces.repositories import TaskRepository


class RecordsService:
    def __init__(
        self, *, task_repository: TaskRepository, embed_queue: TaskEmbedQueue
    ) -> None:
        self.task_repository = task_repository
        self.embed_queue = embed_queue

    async def create_task(
        self,
        *,
        user_id: UUID,
        title: str,
        due_at: datetime | None,
        origin: RecordOrigin,
        original_input: str | None,
    ) -> TaskDTO:
        task = await self.task_repository.create_task(
            user_id=user_id,
            title=title,
            due_at=due_at,
            origin=origin,
            original_input=original_input,
        )
        # Epic 005 AD-7: searchable by meaning once the job runs, after commit.
        await self.embed_queue.queue_task_embed(
            user_id=user_id, task_id=task.id, delay_seconds=0
        )
        return task

    async def list_open_tasks(self, *, user_id: UUID) -> list[TaskDTO]:
        return await self.task_repository.list_open_tasks_for_user(user_id=user_id)

    async def search_candidates(
        self,
        *,
        user_id: UUID,
        terms: Sequence[str],
        query_embedding: Sequence[float] | None,
        max_distance: float,
        limit: int,
    ) -> TaskSearchPageDTO:
        """Epic 005: the user's live tasks a search matches, with the scores
        the search domain ranks by. Ranking is not decided here (AD-1)."""
        return await self.task_repository.search_tasks(
            user_id=user_id,
            terms=terms,
            query_embedding=query_embedding,
            max_distance=max_distance,
            limit=limit,
        )

    async def embedding_of(
        self, *, user_id: UUID, task_id: UUID
    ) -> tuple[float, ...] | None:
        """The live task's stored vector, for related records (005 AD-6)."""
        return await self.task_repository.get_embedding(
            user_id=user_id, task_id=task_id
        )
