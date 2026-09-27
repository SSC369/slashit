"""FR-17: one memory's detail."""

from app.domains.memories.graphql.errors import MemoryNotFoundError
from app.domains.memories.interactors.dtos import GetMemoryInputDTO
from app.domains.memories.interfaces.dtos import MemoryDTO
from app.domains.memories.interfaces.repositories import MemoryRepository


class GetMemoryInteractor:
    def __init__(self, *, memory_repository: MemoryRepository) -> None:
        self.memory_repository = memory_repository

    async def get_memory(self, *, dto: GetMemoryInputDTO) -> MemoryDTO:
        """Return one live memory the caller owns.

        Raises:
            MemoryNotFoundError: no live memory with this id is theirs.
                Forgotten and another user's read the same (NFR-1).
        """
        memory = await self.memory_repository.get_by_id(
            user_id=dto.user_id, memory_id=dto.memory_id
        )
        if memory is None:
            raise MemoryNotFoundError()
        return memory
