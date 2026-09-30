"""Implements search's SearchPort for reminders against the reminders domain."""

from collections.abc import Sequence
from uuid import UUID

from app.domains.reminders.public import ReminderService
from app.domains.search.interfaces.dtos import (
    CandidatePageDTO,
    RecordType,
    SearchCandidate,
)


class ReminderSearchAdapter:
    def __init__(self, *, reminder_service: ReminderService) -> None:
        self.reminder_service = reminder_service

    @property
    def record_type(self) -> RecordType:
        return RecordType.REMINDER

    async def search_candidates(
        self,
        *,
        user_id: UUID,
        terms: Sequence[str],
        query_embedding: Sequence[float] | None,
        max_distance: float,
        limit: int,
    ) -> CandidatePageDTO:
        page = await self.reminder_service.search_candidates(
            user_id=user_id,
            terms=terms,
            query_embedding=query_embedding,
            max_distance=max_distance,
            limit=limit,
        )
        return CandidatePageDTO(
            candidates=[
                SearchCandidate(
                    record_type=RecordType.REMINDER,
                    record_id=match.reminder.id,
                    item=match.reminder,
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
        return await self.reminder_service.embedding_of(
            user_id=user_id, reminder_id=record_id
        )
