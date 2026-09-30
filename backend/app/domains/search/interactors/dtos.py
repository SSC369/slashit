"""Input DTOs for search's use cases."""

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from app.domains.search.interfaces.dtos import RecordType

OpenedEventKind = Literal[
    "search_result_opened", "answer_citation_opened", "related_opened"
]


@dataclass(frozen=True)
class RecordSearchEventInputDTO:
    """PRD section 8: which result or citation was opened, by position."""

    user_id: UUID
    kind: OpenedEventKind
    position: int


@dataclass(frozen=True)
class SearchRecordsInputDTO:
    """FR-22: one page of the records view's search."""

    user_id: UUID
    text: str
    record_type: RecordType | None
    offset: int
    limit: int


@dataclass(frozen=True)
class ListRelatedRecordsInputDTO:
    """FR-25: the record whose detail is open."""

    user_id: UUID
    record_type: RecordType
    record_id: UUID
