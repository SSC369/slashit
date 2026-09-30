"""Give one task its meaning vector. Run by the `records.embed_task` job."""

from app.domains.records.interactors.dtos import EmbedTaskInputDTO
from app.domains.records.interfaces.ports import TaskEmbeddingPort
from app.domains.records.interfaces.repositories import TaskRepository


class EmbedTaskFailedError(Exception):
    """The model refused. Raised so the job's retry strategy runs again; after
    the last attempt the vector stays NULL for the periodic backfill."""


class EmbedTaskInteractor:
    def __init__(
        self, *, task_repository: TaskRepository, embedding: TaskEmbeddingPort
    ) -> None:
        self.task_repository = task_repository
        self.embedding = embedding

    async def embed_task(self, *, dto: EmbedTaskInputDTO) -> bool:
        """Embed the task's current title and store it. False when there is
        nothing to do: the task is gone, already has a vector, or its title
        changed while the model ran (the next queued embed covers that).

        Raises:
            EmbedTaskFailedError: the model refused.
        """
        title = await self.task_repository.get_title_needing_embedding(
            user_id=dto.user_id, task_id=dto.task_id
        )
        if title is None:
            return False
        vector = await self.embedding.embed_task_title(user_id=dto.user_id, title=title)
        if vector is None:
            raise EmbedTaskFailedError()
        return await self.task_repository.set_embedding(
            user_id=dto.user_id, task_id=dto.task_id, title=title, embedding=vector
        )
