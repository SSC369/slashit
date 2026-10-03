"""Implements search's SearchPort for events against the events domain
(epic 007 FR-30, sub-plan 4.2)."""

from collections.abc import Sequence
from uuid import UUID

from app.domains.events.public import EventService
from app.domains.search.interfaces.dtos import (
    CandidatePageDTO,
    RecordType,
    SearchCandidate,
)


class EventSearchAdapter:
    def __init__(self, *, event_service: EventService) -> None:
        self.event_service = event_service

    @property
    def record_type(self) -> RecordType:
        return RecordType.EVENT

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
        """``text`` is unused: only expenses read the whole search (006 Q1)."""
        page = await self.event_service.search_candidates(
            user_id=user_id,
            terms=terms,
            query_embedding=query_embedding,
            max_distance=max_distance,
            limit=limit,
        )
        return CandidatePageDTO(
            candidates=[
                SearchCandidate(
                    record_type=RecordType.EVENT,
                    record_id=match.event.id,
                    item=match.event,
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
        return await self.event_service.embedding_of(
            user_id=user_id, event_id=record_id
        )
