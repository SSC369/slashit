"""Implements capture's MemoryPort against the memories domain."""

from typing import cast
from uuid import UUID

from app.domains.capture.interfaces.ports import MemorySaveOutcome
from app.domains.gateway.public import (
    MalformedResult,
    ProviderTimeout,
    ProviderUnavailable,
    SharedQuotaExhausted,
    UserLimitReached,
)
from app.domains.memories.public import (
    ForgetCandidatesDTO,
    MemoriesForgottenDTO,
    MemoryCountChangedDTO,
    MemoryListDTO,
    MemoryService,
    ModelRefused,
)

_GATEWAY_FAILURES = (
    UserLimitReached,
    ProviderUnavailable,
    ProviderTimeout,
    SharedQuotaExhausted,
    MalformedResult,
)


class MemoriesAdapter:
    def __init__(self, *, memory_service: MemoryService) -> None:
        self.memory_service = memory_service

    async def save_memory(
        self, *, user_id: UUID, text: str, original_input: str
    ) -> MemorySaveOutcome:
        outcome = await self.memory_service.save_memory(
            user_id=user_id, text=text, original_input=original_input
        )
        if not isinstance(outcome, ModelRefused):
            return outcome
        # Memories carries the gateway's member opaque; this adapter is the
        # one place in capture that knows both sides, so it unwraps it here.
        if isinstance(outcome.gateway_result, _GATEWAY_FAILURES):
            return cast(MemorySaveOutcome, outcome.gateway_result)
        return ProviderUnavailable(message="The model provider is unavailable")

    async def list_memories(self, *, user_id: UUID) -> MemoryListDTO:
        return await self.memory_service.list_memories(user_id=user_id)

    async def look_up_memories(self, *, user_id: UUID, text: str) -> MemoryListDTO:
        return await self.memory_service.look_up_memories(user_id=user_id, text=text)

    async def find_forget_candidates(
        self, *, user_id: UUID, text: str
    ) -> ForgetCandidatesDTO:
        return await self.memory_service.find_forget_candidates(
            user_id=user_id, text=text
        )

    async def forget_memories(
        self, *, user_id: UUID, memory_ids: list[UUID]
    ) -> MemoriesForgottenDTO:
        return await self.memory_service.forget_memories(
            user_id=user_id, memory_ids=memory_ids
        )

    async def forget_all(
        self, *, user_id: UUID, expected_count: int
    ) -> MemoriesForgottenDTO | MemoryCountChangedDTO:
        return await self.memory_service.forget_all(
            user_id=user_id, expected_count=expected_count
        )
