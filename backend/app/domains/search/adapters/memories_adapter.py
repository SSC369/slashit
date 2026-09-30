"""Implements search's SearchPort for memories against the memories domain."""

from collections.abc import Sequence
from uuid import UUID

from app.domains.memories.public import MemoryService
from app.domains.search.interfaces.dtos import (
    CandidatePageDTO,
    RecordType,
    SearchCandidate,
)


class MemorySearchAdapter:
    def __init__(self, *, memory_service: MemoryService) -> None:
        self.memory_service = memory_service

    @property
    def record_type(self) -> RecordType:
        return RecordType.MEMORY

    async def search_candidates(
        self,
        *,
        user_id: UUID,
        terms: Sequence[str],
        query_embedding: Sequence[float] | None,
        max_distance: float,
        limit: int,
    ) -> CandidatePageDTO:
        page = await self.memory_service.search_candidates(
            user_id=user_id,
            terms=terms,
            query_embedding=query_embedding,
            max_distance=max_distance,
            limit=limit,
        )
        return CandidatePageDTO(
            candidates=[
                SearchCandidate(
                    record_type=RecordType.MEMORY,
                    record_id=match.memory.id,
                    item=match.memory,
                    all_terms=match.all_terms,
                    word_rank=match.word_rank,
                    distance=match.distance,
                )
                for match in page.matches
            ],
            total=page.total,
        )

    async def embedding_of(
        self, *, user_id: UUID, record_id: UUID
    ) -> tuple[float, ...] | None:
        return await self.memory_service.embedding_of(
            user_id=user_id, memory_id=record_id
        )
