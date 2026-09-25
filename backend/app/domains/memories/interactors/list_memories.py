"""FR-15, FR-16: the Memories tab."""

from app.domains.memories.interactors.dtos import ListMemoriesInputDTO
from app.domains.memories.interfaces.dtos import MemoryDTO
from app.domains.memories.interfaces.repositories import MemoryRepository


class ListMemoriesInteractor:
    def __init__(self, *, memory_repository: MemoryRepository) -> None:
        self.memory_repository = memory_repository

    async def list_memories(self, *, dto: ListMemoriesInputDTO) -> list[MemoryDTO]:
        """The caller's live memories, newest first, filtered by category."""
        search = dto.search.strip() if dto.search else None
        return await self.memory_repository.list_for_user(
            user_id=dto.user_id, category=dto.category, search=search or None
        )
