"""Memories' published service: save, list and look up.

Capture calls it for `/remember`, `/add-memory` and `/memories`; records calls
it for the All tab. Other domains reach it only through ``public.py``.
"""

from uuid import UUID

import structlog

from app.domains.memories.constants import (
    FORGET_ALL_PHRASES,
    FORGET_PICK_LIMIT,
    LOOKUP_LIMIT,
    MAX_FACT_LENGTH,
)
from app.domains.memories.interfaces.dtos import (
    ForgetCandidatesDTO,
    MemoriesForgottenDTO,
    MemoryCountChangedDTO,
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
    TurnScrubPort,
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
        turn_scrub: TurnScrubPort,
    ) -> None:
        self.memory_repository = memory_repository
        self.embedding = embedding
        self.judgement = judgement
        self.analytics = analytics
        self.turn_scrub = turn_scrub

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

    async def find_forget_candidates(
        self, *, user_id: UUID, text: str
    ) -> ForgetCandidatesDTO:
        """What `/forget <which>` offers. Forgets nothing (FR-24 to FR-27).

        One of the exact forget-all phrases offers every memory, by count;
        anything else is a word match, capped at five (sub-plan 4.2, Q2, Q4).
        Never calls the model, so forget works while the model is down.
        """
        search_text = text.strip()
        if search_text.lower() in FORGET_ALL_PHRASES:
            live_ids = await self.memory_repository.list_live_ids(user_id=user_id)
            return ForgetCandidatesDTO(
                search_text=search_text,
                candidates=[],
                total_matches=0,
                forget_all=True,
                all_count=len(live_ids),
            )
        terms = build_lookup_terms(text=search_text)
        candidates = await self.memory_repository.find_by_terms(
            user_id=user_id, terms=terms, limit=FORGET_PICK_LIMIT
        )
        total_matches = await self.memory_repository.count_by_terms(
            user_id=user_id, terms=terms
        )
        return ForgetCandidatesDTO(
            search_text=search_text,
            candidates=candidates,
            total_matches=total_matches,
            forget_all=False,
            all_count=0,
        )

    async def forget_memories(
        self, *, user_id: UUID, memory_ids: list[UUID]
    ) -> MemoriesForgottenDTO:
        """Forget the caller's live memories among ``memory_ids`` (FR-22, FR-23).

        The history scrub runs before the tombstone. If the tombstone then
        fails, the memory is still visible and a retry finishes the job; the
        other order could strand the fact's words in history (sub-plan 4.2 §5).
        """
        live_ids = await self.memory_repository.filter_live_ids(
            user_id=user_id, memory_ids=memory_ids
        )
        if not live_ids:
            return MemoriesForgottenDTO(count=0)
        await self.turn_scrub.scrub_turns_for_memories(
            user_id=user_id, memory_ids=live_ids
        )
        forgotten_count = await self.memory_repository.tombstone_memories(
            user_id=user_id, memory_ids=live_ids
        )
        await self._record_event(user_id=user_id, event_type="memory_forgotten")
        return MemoriesForgottenDTO(count=forgotten_count)

    async def forget_all(
        self, *, user_id: UUID, expected_count: int
    ) -> MemoriesForgottenDTO | MemoryCountChangedDTO:
        """FR-27: forget every memory, but only the number the user confirmed.
        A memory saved in another tab since then changes the count, and
        nothing is forgotten until the user confirms again."""
        live_ids = await self.memory_repository.list_live_ids(user_id=user_id)
        if len(live_ids) != expected_count:
            return MemoryCountChangedDTO(count=len(live_ids))
        return await self.forget_memories(user_id=user_id, memory_ids=live_ids)

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
