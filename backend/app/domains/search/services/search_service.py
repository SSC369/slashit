"""Search's published service. Capture calls it for `/search`; slice 3's
records view search and related records call it too. Other domains reach it
only through ``public.py``.
"""

import asyncio
import time
from collections.abc import Sequence
from uuid import UUID

import structlog

from app.domains.search.constants import (
    GROUP_LIMIT,
    MEANING_MAX_DISTANCE,
    PORT_LIMIT,
)
from app.domains.search.interfaces.dtos import (
    CandidatePageDTO,
    RecordType,
    SearchResultsDTO,
)
from app.domains.search.interfaces.ports import (
    QueryEmbeddingPort,
    SearchAnalyticsPort,
    SearchPort,
)
from app.domains.search.services.ranking import group_hits
from app.domains.search.services.terms import build_terms

logger = structlog.get_logger(__name__)


class SearchService:
    def __init__(
        self,
        *,
        search_ports: Sequence[SearchPort],
        query_embedding: QueryEmbeddingPort,
        analytics: SearchAnalyticsPort,
    ) -> None:
        self.search_ports = search_ports
        self.query_embedding = query_embedding
        self.analytics = analytics

    @property
    def covered_record_types(self) -> set[RecordType]:
        """AD-11: the record types this search reaches."""
        return {port.record_type for port in self.search_ports}

    async def search_for_capture(self, *, user_id: UUID, text: str) -> SearchResultsDTO:
        """`/search <text>`: every record type, by words and meaning, grouped.

        The query's vector is fetched while the word pass runs (AD-4). With a
        vector, one more pass matches by both and replaces the word-only
        results; without one, the word matches stand, flagged (FR-20).
        """
        terms = build_terms(text=text)
        started = time.monotonic()
        query_vector, word_pages = await asyncio.gather(
            self.query_embedding.embed_query(user_id=user_id, text=text),
            self._search_every_type(user_id=user_id, terms=terms, query_vector=None),
        )
        words_done = time.monotonic()
        pages = word_pages
        if query_vector is not None:
            pages = await self._search_every_type(
                user_id=user_id, terms=terms, query_vector=query_vector
            )
        results = SearchResultsDTO(
            query=text,
            groups=group_hits(
                candidates=[
                    candidate
                    for page in pages.values()
                    for candidate in page.candidates
                ],
                totals={record_type: page.total for record_type, page in pages.items()},
                limit=GROUP_LIMIT,
            ),
            meaning_unavailable=query_vector is None,
        )
        # Stage timings and counts only: never the text (AD-10).
        logger.info(
            "search.searched",
            words_and_embed_ms=round((words_done - started) * 1000),
            total_ms=round((time.monotonic() - started) * 1000),
            meaning_unavailable=query_vector is None,
            group_count=len(results.groups),
        )
        await self.analytics.record_search_run(user_id=user_id)
        return results

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
