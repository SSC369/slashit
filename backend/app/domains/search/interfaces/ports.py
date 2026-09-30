"""What search needs from other domains, in its own words.

Per repo-rules.md section 6, the port belongs to the consumer. Search holds no
data: every record it returns comes through a ``SearchPort``, one per record
type, each implemented by an adapter over that domain's ``public.py`` (AD-1).
"""

from collections.abc import Sequence
from datetime import date
from typing import Literal, Protocol
from uuid import UUID

from app.domains.search.interfaces.dtos import (
    AnswerDraftDTO,
    AnswerRecordDTO,
    CandidatePageDTO,
    RecordType,
)


class SearchPort(Protocol):
    """One record type's search. Matches when any term is present or the
    record is within ``max_distance`` of the query vector; deleted records
    never match; every call runs as the user, under Row Level Security."""

    @property
    def record_type(self) -> RecordType: ...

    async def search_candidates(
        self,
        *,
        user_id: UUID,
        terms: Sequence[str],
        query_embedding: Sequence[float] | None,
        max_distance: float,
        limit: int,
    ) -> CandidatePageDTO: ...

    async def embedding_of(
        self, *, user_id: UUID, record_id: UUID
    ) -> tuple[float, ...] | None: ...


class QueryEmbeddingPort(Protocol):
    """The meaning of a search's text. None on a timeout, a provider error or
    an exhausted quota: the caller then searches by words only (FR-20)."""

    async def embed_query(
        self, *, user_id: UUID, text: str
    ) -> tuple[float, ...] | None: ...


class AnswerPort(Protocol):
    """FR-16: a written answer from the numbered records and nothing else.
    None on any gateway failure, the per-user cap included (FR-19)."""

    async def write_answer(
        self,
        *,
        user_id: UUID,
        question: str,
        today: date,
        records: Sequence[AnswerRecordDTO],
    ) -> AnswerDraftDTO | None: ...


class UserTimezonePort(Protocol):
    """Where the user is, so "today" and a record's dates read in their zone."""

    async def get_user_timezone(self, *, user_id: UUID) -> str: ...


# PRD section 8. Numbers and booleans only, never text (AD-10, migration 0036).
SearchEventProperties = dict[str, int | float | bool]

SearchEventType = Literal[
    "search_run", "search_result_opened", "answer_citation_opened", "related_opened"
]


class SearchAnalyticsPort(Protocol):
    """PRD section 8's events. Never the search text (AD-10)."""

    async def record_search_event(
        self,
        *,
        user_id: UUID,
        event_type: SearchEventType,
        properties: SearchEventProperties,
    ) -> None: ...
