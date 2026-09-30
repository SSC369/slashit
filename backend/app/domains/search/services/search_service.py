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
)
from app.domains.search.interfaces.dtos import (
    CandidatePageDTO,
    RecordType,
    SearchAnswerDTO,
    SearchCandidate,
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

        The query's vector is fetched while the word pass runs (AD-4). With a
        vector, one more pass matches by both and replaces the word-only
        results; without one, the word matches stand, flagged (FR-20). A
        question then gets a checked, cited answer from the top ten (FR-15 to
        FR-19); a word search never calls the model for one.
        """
        terms = build_terms(text=text)
        started = time.monotonic()
        query_vector, word_pages = await asyncio.gather(
            self.query_embedding.embed_query(user_id=user_id, text=text),
            self._search_every_type(user_id=user_id, terms=terms, query_vector=None),
        )
        pages = word_pages
        if query_vector is not None:
            pages = await self._search_every_type(
                user_id=user_id, terms=terms, query_vector=query_vector
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
        if draft is None:
            return _AnswerOutcome(
                answer=None, citations={}, no_support=False, answer_unavailable=True
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
                limit=PORT_LIMIT,
            )
        return pages
