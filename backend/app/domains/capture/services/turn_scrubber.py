"""Erases the words of capture turns that saved forgotten memories. FR-23.

Satisfies memories' ``TurnScrubPort`` structurally. It is a service, not an
adapter: it imports nothing from memories, which already depends on nothing in
capture, so the domain graph stays acyclic (build plan §2). ``core/deps.py``
hands it to ``MemoryService``.
"""

from uuid import UUID

from app.domains.capture.interfaces.repositories import CaptureTurnRepository


class CaptureTurnScrubber:
    def __init__(self, *, capture_turn_repository: CaptureTurnRepository) -> None:
        self.capture_turn_repository = capture_turn_repository

    async def scrub_turns_for_memories(
        self, *, user_id: UUID, memory_ids: list[UUID]
    ) -> int:
        return await self.capture_turn_repository.scrub_turns_for_memories(
            user_id=user_id, memory_ids=memory_ids
        )
