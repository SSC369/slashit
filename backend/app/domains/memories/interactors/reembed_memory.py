"""Refresh one memory's vector after an edit. Run by the `memories.reembed` job."""

from app.domains.memories.interactors.dtos import ReembedMemoryInputDTO
from app.domains.memories.interfaces.dtos import ModelRefused
from app.domains.memories.interfaces.ports import EmbeddingPort
from app.domains.memories.interfaces.repositories import MemoryRepository


class ReembedFailedError(Exception):
    """The model refused. Raised so the job's retry strategy runs again; after
    the last attempt the vector stays NULL and the memory is simply not a
    conflict candidate (build plan §6)."""


class ReembedMemoryInteractor:
    def __init__(
        self, *, memory_repository: MemoryRepository, embedding: EmbeddingPort
    ) -> None:
        self.memory_repository = memory_repository
        self.embedding = embedding

    async def reembed_memory(self, *, dto: ReembedMemoryInputDTO) -> bool:
        """Embed the memory's current text and store it. False when the memory
        is gone, which is not a failure: it was forgotten after the edit.

        Raises:
            ReembedFailedError: the model refused.
        """
        memory = await self.memory_repository.get_by_id(
            user_id=dto.user_id, memory_id=dto.memory_id
        )
        if memory is None:
            return False
        vector = await self.embedding.embed_fact(user_id=dto.user_id, text=memory.text)
        if isinstance(vector, ModelRefused):
            raise ReembedFailedError()
        await self.memory_repository.set_embedding(
            user_id=dto.user_id, memory_id=dto.memory_id, embedding=vector
        )
        return True
