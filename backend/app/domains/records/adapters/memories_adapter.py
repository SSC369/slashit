"""Implements records' MemoryRecordsPort against the memories domain."""

from uuid import UUID

from app.domains.memories.public import MemoryDTO, MemoryService


class MemoryRecordsAdapter:
    def __init__(self, *, memory_service: MemoryService) -> None:
        self.memory_service = memory_service

    async def list_memories(
        self, *, user_id: UUID, search: str | None
    ) -> list[MemoryDTO]:
        return await self.memory_service.list_for_records(
            user_id=user_id, search=search
        )
