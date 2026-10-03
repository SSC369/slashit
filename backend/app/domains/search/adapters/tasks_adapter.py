"""Implements search's SearchPort for tasks against the records domain."""

from collections.abc import Sequence
from uuid import UUID

from app.domains.records.public import RecordsService
from app.domains.search.interfaces.dtos import (
    CandidatePageDTO,
    RecordType,
    SearchCandidate,
)


class TaskSearchAdapter:
    def __init__(self, *, records_service: RecordsService) -> None:
        self.records_service = records_service

    @property
    def record_type(self) -> RecordType:
        return RecordType.TASK

    async def search_candidates(
        self,
        *,
        user_id: UUID,
        text: str,
        terms: Sequence[str],
        query_embedding: Sequence[float] | None,
        max_distance: float,
        limit: int,
    ) -> CandidatePageDTO:
        page = await self.records_service.search_candidates(
            user_id=user_id,
            terms=terms,
            query_embedding=query_embedding,
            max_distance=max_distance,
            limit=limit,
        )
        return CandidatePageDTO(
            candidates=[
                SearchCandidate(
                    record_type=RecordType.TASK,
                    record_id=match.task.id,
                    item=match.task,
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
        return await self.records_service.embedding_of(
            user_id=user_id, task_id=record_id
        )
