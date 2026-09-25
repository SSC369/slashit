"""Memories' published service: save, list and look up.

Capture calls it for `/remember`, `/add-memory` and `/memories`; records calls
it for the All tab. Other domains reach it only through ``public.py``.
"""

from uuid import UUID

import structlog

from app.domains.memories.constants import LOOKUP_LIMIT, MAX_FACT_LENGTH
from app.domains.memories.interfaces.dtos import (
    MemoryDTO,
    MemoryListDTO,
    MemorySavedDTO,
    MemoryTooLongDTO,
    ModelRefused,
)
from app.domains.memories.interfaces.ports import (
    EmbeddingPort,
    JudgementPort,
    MemoryAnalyticsPort,
    MemoryEventType,
)
from app.domains.memories.interfaces.repositories import MemoryRepository, MemoryWrite
from app.domains.memories.services.keyword_query import build_lookup_terms
from app.domains.memories.services.secret_check import detect_secret

logger = structlog.get_logger(__name__)

SaveOutcome = MemorySavedDTO | MemoryTooLongDTO | ModelRefused


class MemoryService:
    def __init__(
        self,
        *,
        memory_repository: MemoryRepository,
        embedding: EmbeddingPort,
        judgement: JudgementPort,
        analytics: MemoryAnalyticsPort,
    ) -> None:
        self.memory_repository = memory_repository
        self.embedding = embedding
        self.judgement = judgement
        self.analytics = analytics

    async def save_memory(
        self, *, user_id: UUID, text: str, original_input: str
    ) -> SaveOutcome:
        """Save one fact, in the user's own words (FR-2).

        Nothing is written until both model calls have succeeded, so a failure
        in either leaves no row (FR-9). The caution is decided before any call,
        and never blocks the save (FR-8).
        """
        fact = text.strip()
        if len(fact) > MAX_FACT_LENGTH:
            return MemoryTooLongDTO(length=len(fact))
        secret_caution = detect_secret(text=fact)

        vector = await self.embedding.embed_fact(user_id=user_id, text=fact)
        if isinstance(vector, ModelRefused):
            return vector
        judgement = await self.judgement.judge_fact(
            user_id=user_id, text=fact, candidates=[]
        )
        if isinstance(judgement, ModelRefused):
            return judgement

        memory = await self.memory_repository.create_memory(
            user_id=user_id,
            write=MemoryWrite(
                text=fact,
                category=judgement.category,
                embedding=vector,
                origin="command",
                original_input=original_input,
            ),
        )
        await self._record_event(user_id=user_id, event_type="memory_saved")
        if secret_caution is not None:
            await self._record_event(
                user_id=user_id, event_type="memory_secret_caution"
            )
        return MemorySavedDTO(memory=memory, secret_caution=secret_caution)

    async def list_memories(self, *, user_id: UUID) -> MemoryListDTO:
        """FR-19: every live memory, newest first."""
        memories = await self.memory_repository.list_for_user(
            user_id=user_id, category=None, search=None
        )
        return MemoryListDTO(memories=memories, search_text=None)

    async def look_up_memories(self, *, user_id: UUID, text: str) -> MemoryListDTO:
        """FR-20: memories containing any of the text's words, most matches
        first. Words, not meaning: related-meaning lookup is epic 005."""
        terms = build_lookup_terms(text=text)
        memories = await self.memory_repository.find_by_terms(
            user_id=user_id, terms=terms, limit=LOOKUP_LIMIT
        )
        await self._record_event(user_id=user_id, event_type="memory_lookup")
        return MemoryListDTO(memories=memories, search_text=text)

    async def list_for_records(
        self, *, user_id: UUID, search: str | None
    ) -> list[MemoryDTO]:
        """Every live memory for the records All tab (FR-15)."""
        return await self.memory_repository.list_for_user(
            user_id=user_id, category=None, search=search
        )

    async def _record_event(
        self, *, user_id: UUID, event_type: MemoryEventType
    ) -> None:
        """Instrumentation never turns a successful save into an error, the
        same rule capture's ``_record_turn`` follows."""
        try:
            await self.analytics.record_memory_event(
                user_id=user_id, event_type=event_type
            )
        except Exception:
            # Broad on purpose: any failure here is an instrumentation loss,
            # logged, never the user's problem.
            logger.exception(
                "memories.event_not_recorded",
                user_id=str(user_id),
                event_type=event_type,
            )
