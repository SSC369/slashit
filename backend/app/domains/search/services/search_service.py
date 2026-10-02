"""Search's published service. Capture calls it for `/search`; slice 3's
records view search and related records call it too. Other domains reach it
only through ``public.py``.
"""

import asyncio
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

import structlog

from app.domains.search.constants import (
    ANSWER_RECORD_LIMIT,
    GROUP_LIMIT,
    MEANING_MAX_DISTANCE,
    PORT_LIMIT,
    RELATED_LIMIT,
    RELATED_MAX_DISTANCE,
)
from app.domains.search.interfaces.dtos import (
    AnswerRefusedDTO,
    CandidatePageDTO,
    RecordType,
    RelatedRecordDTO,
    SearchAnswerDTO,
    SearchCandidate,
    SearchHitDTO,
    SearchPageDTO,
    SearchResultsDTO,
)
from app.domains.search.interfaces.ports import (
    AnswerPort,
    QueryEmbeddingPort,
    SearchAnalyticsPort,
    SearchPort,
    UserTimezonePort,
)
from app.domains.search.services.answer_check import check_answer
from app.domains.search.services.answer_records import describe_record
from app.domains.search.services.question import is_question
from app.domains.search.services.ranking import group_hits, rank_key
from app.domains.search.services.terms import build_terms

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class _AnswerOutcome:
    """What the answer step produced, for the results and the event."""

    answer: SearchAnswerDTO | None
    citations: dict[UUID, int]
    no_support: bool
    answer_unavailable: bool
    answer_limit_reached: bool = False


_NO_ANSWER = _AnswerOutcome(
    answer=None, citations={}, no_support=False, answer_unavailable=False
)


class SearchService:
    def __init__(
        self,
        *,
        search_ports: Sequence[SearchPort],
        query_embedding: QueryEmbeddingPort,
        answer: AnswerPort,
        user_timezone: UserTimezonePort,
        analytics: SearchAnalyticsPort,
        now_provider: Callable[[], datetime],
    ) -> None:
        self.search_ports = search_ports
        self.query_embedding = query_embedding
        self.answer = answer
        self.user_timezone = user_timezone
        self.analytics = analytics
        self.now_provider = now_provider

    @property
    def covered_record_types(self) -> set[RecordType]:
        """AD-11: the record types this search reaches."""
        return {port.record_type for port in self.search_ports}

    async def search_for_capture(self, *, user_id: UUID, text: str) -> SearchResultsDTO:
        """`/search <text>`: every record type, by words and meaning, grouped.

        Word matches stand, flagged, when the meaning call fails (FR-20). A
        question then gets a checked, cited answer from the top ten (FR-15 to
        FR-19); a word search never calls the model for one.
        """
        started = time.monotonic()
        pages, query_vector = await self._search_by_words_and_meaning(
            user_id=user_id, text=text, limit=PORT_LIMIT
        )
        searched = time.monotonic()
        candidates = [
            candidate for page in pages.values() for candidate in page.candidates
        ]
        asked = is_question(text=text)
        outcome = (
            await self._answer_question(
                user_id=user_id, question=text, candidates=candidates
            )
            if asked
            else _NO_ANSWER
        )
        results = SearchResultsDTO(
            query=text,
            groups=group_hits(
                candidates=candidates,
                totals={record_type: page.total for record_type, page in pages.items()},
                limit=GROUP_LIMIT,
                citations=outcome.citations,
            ),
            meaning_unavailable=query_vector is None,
            answer=outcome.answer,
            no_support=outcome.no_support,
            answer_unavailable=outcome.answer_unavailable,
            answer_limit_reached=outcome.answer_limit_reached,
        )
        # Stage timings and counts only: never the text (AD-10).
        logger.info(
            "search.searched",
            search_ms=round((searched - started) * 1000),
            answer_ms=round((time.monotonic() - searched) * 1000),
            is_question=asked,
            meaning_unavailable=query_vector is None,
            group_count=len(results.groups),
        )
        await self.analytics.record_search_event(
            user_id=user_id,
            event_type="search_run",
            properties={
                "result_count": sum(group.total for group in results.groups),
                "group_count": len(results.groups),
                "is_question": asked,
                "answered": results.answer is not None,
                "no_support": results.no_support,
                "meaning_unavailable": results.meaning_unavailable,
                "answer_unavailable": results.answer_unavailable,
            },
        )
        return results

    async def search_page(
        self,
        *,
        user_id: UUID,
        text: str,
        record_type: RecordType | None,
        offset: int,
        limit: int,
    ) -> SearchPageDTO:
        """FR-22 to FR-24: the records view's search. The same passes and the
        same ranking as `/search`, so the same text finds the same records;
        never an answer. Each port returns enough to fill the page asked for."""
        pages, query_vector = await self._search_by_words_and_meaning(
            user_id=user_id, text=text, limit=offset + limit
        )
        ranked = sorted(
            (
                candidate
                for page in pages.values()
                for candidate in page.candidates
                if record_type is None or candidate.record_type == record_type
            ),
            key=rank_key,
        )
        total = sum(
            page.total
            for page_type, page in pages.items()
            if record_type is None or page_type == record_type
        )
        return SearchPageDTO(
            query=text,
            hits=[
                SearchHitDTO(
                    record_type=candidate.record_type,
                    item=candidate.item,
                    citation=None,
                )
                for candidate in ranked[offset : offset + limit]
            ],
            total=total,
            other_types_total=sum(page.total for page in pages.values()) - total,
            meaning_unavailable=query_vector is None,
        )

    async def related(
        self, *, user_id: UUID, record_type: RecordType, record_id: UUID
    ) -> list[RelatedRecordDTO]:
        """FR-25 to FR-27, AD-6: the records nearest in meaning to this one,
        across every type, from its stored vector. No model call. A record
        with no vector yet, or one this user cannot see, has none."""
        source_port = next(
            port for port in self.search_ports if port.record_type == record_type
        )
        vector = await source_port.embedding_of(user_id=user_id, record_id=record_id)
        if vector is None:
            return []
        candidates: list[SearchCandidate] = []
        for port in self.search_ports:
            page = await port.search_candidates(
                user_id=user_id,
                terms=[],
                query_embedding=vector,
                max_distance=RELATED_MAX_DISTANCE,
                # One more than shown: the record itself is among them.
                limit=RELATED_LIMIT + 1,
            )
            candidates.extend(page.candidates)
        nearest = sorted(
            (
                candidate
                for candidate in candidates
                if candidate.record_id != record_id and candidate.distance is not None
            ),
            key=lambda candidate: candidate.distance or 0.0,
        )
        return [
            RelatedRecordDTO(record_type=candidate.record_type, item=candidate.item)
            for candidate in nearest[:RELATED_LIMIT]
        ]

    async def _search_by_words_and_meaning(
        self, *, user_id: UUID, text: str, limit: int
    ) -> tuple[dict[RecordType, CandidatePageDTO], tuple[float, ...] | None]:
        """AD-4: the query's vector is fetched while the word pass runs. With
        a vector, one more pass matches by both and replaces the word-only
        results; without one, the word matches stand (FR-20)."""
        terms = build_terms(text=text)
        query_vector, word_pages = await asyncio.gather(
            self.query_embedding.embed_query(user_id=user_id, text=text),
            self._search_every_type(
                user_id=user_id, terms=terms, query_vector=None, limit=limit
            ),
        )
        if query_vector is None:
            return word_pages, None
        pages = await self._search_every_type(
            user_id=user_id, terms=terms, query_vector=query_vector, limit=limit
        )
        return pages, query_vector

    async def _answer_question(
        self, *, user_id: UUID, question: str, candidates: list[SearchCandidate]
    ) -> _AnswerOutcome:
        """FR-16 to FR-19. No record at all needs no model to say so."""
        top = sorted(candidates, key=rank_key)[:ANSWER_RECORD_LIMIT]
        if not top:
            return _AnswerOutcome(
                answer=None, citations={}, no_support=True, answer_unavailable=False
            )
        timezone = ZoneInfo(await self.user_timezone.get_user_timezone(user_id=user_id))
        draft = await self.answer.write_answer(
            user_id=user_id,
            question=question,
            today=self.now_provider().astimezone(timezone).date(),
            records=[
                describe_record(
                    number=number,
                    record_type=candidate.record_type,
                    item=candidate.item,
                    timezone=timezone,
                )
                for number, candidate in enumerate(top, start=1)
            ],
        )
        if isinstance(draft, AnswerRefusedDTO):
            return _AnswerOutcome(
                answer=None,
                citations={},
                no_support=False,
                answer_unavailable=True,
                answer_limit_reached=draft.limit_reached,
            )
        checked = check_answer(draft=draft, record_count=len(top))
        if checked is None:
            return _AnswerOutcome(
                answer=None, citations={}, no_support=True, answer_unavailable=False
            )
        return _AnswerOutcome(
            answer=SearchAnswerDTO(sentences=checked.sentences),
            citations={
                top[number - 1].record_id: citation
                for citation, number in enumerate(checked.cited_numbers, start=1)
            },
            no_support=False,
            answer_unavailable=False,
        )

    async def _search_every_type(
        self,
        *,
        user_id: UUID,
        terms: Sequence[str],
        query_vector: Sequence[float] | None,
        limit: int,
    ) -> dict[RecordType, CandidatePageDTO]:
        """One pass over every record type. Sequential on purpose: the ports
        share the request's database session, which runs one query at a time."""
        pages: dict[RecordType, CandidatePageDTO] = {}
        for port in self.search_ports:
            pages[port.record_type] = await port.search_candidates(
                user_id=user_id,
                terms=terms,
                query_embedding=query_vector,
                max_distance=MEANING_MAX_DISTANCE,
                limit=limit,
            )
        return pages
