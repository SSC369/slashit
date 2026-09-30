from app.domains.records.graphql.errors import (
    NoFieldsToUpdateError,
    RecordNotFoundError,
)
from app.domains.records.interactors.dtos import UpdateTaskInputDTO
from app.domains.records.interfaces.dtos import TaskDTO
from app.domains.records.interfaces.ports import TaskEmbedQueue
from app.domains.records.interfaces.repositories import TaskRepository


class UpdateTaskInteractor:
    def __init__(
        self, *, task_repository: TaskRepository, embed_queue: TaskEmbedQueue
    ) -> None:
        self.task_repository = task_repository
        self.embed_queue = embed_queue

    async def update_task(self, *, dto: UpdateTaskInputDTO) -> TaskDTO:
        """Change the title, the status, the due date, or any combination, of
        one task the caller owns.

        Raises:
            NoFieldsToUpdateError: no field was supplied.
            RecordNotFoundError: no task with this id belongs to this user.
        """
        self._validate_has_a_field(
            title=dto.title, status=dto.status, due_at_provided=dto.due_at_provided
        )

        task = await self.task_repository.update(
            user_id=dto.user_id,
            task_id=dto.task_id,
            title=dto.title,
            status=dto.status,
            due_at=dto.due_at,
            due_at_provided=dto.due_at_provided,
        )
        if task is None:
            raise RecordNotFoundError()
        await self._queue_embed_after_title_edit(task=task, title=dto.title)
        return task

    async def _queue_embed_after_title_edit(
        self, *, task: TaskDTO, title: str | None
    ) -> None:
        """Epic 005 FR-14: a changed title lost its vector in the update. The
        job re-embeds it, and does nothing if the title was unchanged."""
        if title is None:
            return
        await self.embed_queue.queue_task_embed(
            user_id=task.user_id, task_id=task.id, delay_seconds=0
        )

    def _validate_has_a_field(
        self, *, title: str | None, status: str | None, due_at_provided: bool
    ) -> None:
        if title is None and status is None and not due_at_provided:
            raise NoFieldsToUpdateError()
