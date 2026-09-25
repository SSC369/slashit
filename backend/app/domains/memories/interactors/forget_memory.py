"""FR-21, FR-22: forget one memory from its detail page."""

from app.domains.memories.graphql.errors import MemoryNotFoundError
from app.domains.memories.interactors.dtos import ForgetMemoryInputDTO
from app.domains.memories.interfaces.dtos import MemoriesForgottenDTO
from app.domains.memories.services.memory_service import MemoryService


class ForgetMemoryInteractor:
    def __init__(self, *, memory_service: MemoryService) -> None:
        self.memory_service = memory_service

    async def forget_memory(self, *, dto: ForgetMemoryInputDTO) -> MemoriesForgottenDTO:
        """Forget one live memory the caller owns. Writes no capture turn:
        nothing was typed, and the turn that saved it is scrubbed.

        Raises:
            MemoryNotFoundError: no live memory with this id is theirs.
                Already forgotten and another user's read the same.
        """
        forgotten = await self.memory_service.forget_memories(
            user_id=dto.user_id, memory_ids=[dto.memory_id]
        )
        if forgotten.count == 0:
            raise MemoryNotFoundError()
        return forgotten
