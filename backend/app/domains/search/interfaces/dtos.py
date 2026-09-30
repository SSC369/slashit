"""Data crossing search's boundaries. Frozen, never a model instance.

The GraphQL shapes live here too, not under ``graphql/``, so capture may carry
them in its result union (repo-rules.md section 6.2), as records does for
``Task``.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated
from uuid import UUID

import strawberry

from app.domains.memories.public import Memory, MemoryDTO, memory_dto_to_type
from app.domains.records.public import Task, TaskDTO, task_dto_to_type
from app.domains.reminders.public import Reminder, ReminderDTO, reminder_dto_to_type
from app.domains.search.constants import MAX_SEARCH_LENGTH

RecordDTO = TaskDTO | ReminderDTO | MemoryDTO


@strawberry.enum
class RecordType(StrEnum):
    TASK = "task"
    REMINDER = "reminder"
    MEMORY = "memory"


@dataclass(frozen=True)
class SearchCandidate:
    """One record a record domain matched, with the scores ranking reads.

    ``word_rank`` is None when no term is present; ``distance`` is None when
    the record has no vector yet or the search had none (index §5).
    """

    record_type: RecordType
    record_id: UUID
    item: RecordDTO
    all_terms: bool
    word_rank: float | None
    distance: float | None


@dataclass(frozen=True)
class CandidatePageDTO:
    """One record domain's answer: its best candidates and how many matched."""

    candidates: list[SearchCandidate]
    total: int


@dataclass(frozen=True)
class SearchHitDTO:
    record_type: RecordType
    item: RecordDTO
    # Always None until slice 2's written answer cites records.
    citation: int | None


@dataclass(frozen=True)
class SearchGroupDTO:
    record_type: RecordType
    hits: list[SearchHitDTO]
    total: int


@dataclass(frozen=True)
class SearchResultsDTO:
    """FR-7: groups ordered by each group's best hit; empty when nothing
    matched (FR-10)."""

    query: str
    groups: list[SearchGroupDTO]
    meaning_unavailable: bool


@dataclass(frozen=True)
class SearchTooLongDTO:
    """FR-3: nothing was searched; the client keeps the text."""

    length: int
    limit: int = MAX_SEARCH_LENGTH


SearchRecord = Annotated[Task | Reminder | Memory, strawberry.union("SearchRecord")]


@strawberry.type
class SearchHit:
    citation: int | None
    record: SearchRecord


@strawberry.type
class SearchGroup:
    record_type: RecordType
    total: int
    hits: list[SearchHit]


@strawberry.type
class SearchResults:
    query: str
    groups: list[SearchGroup]
    meaning_unavailable: bool


@strawberry.type
class SearchTooLong:
    length: int
    limit: int


def search_results_to_type(*, results: SearchResultsDTO) -> SearchResults:
    return SearchResults(
        query=results.query,
        groups=[
            SearchGroup(
                record_type=group.record_type,
                total=group.total,
                hits=[
                    SearchHit(
                        citation=hit.citation, record=_record_to_type(item=hit.item)
                    )
                    for hit in group.hits
                ],
            )
            for group in results.groups
        ],
        meaning_unavailable=results.meaning_unavailable,
    )


def search_too_long_to_type(*, too_long: SearchTooLongDTO) -> SearchTooLong:
    return SearchTooLong(length=too_long.length, limit=too_long.limit)


def _record_to_type(*, item: RecordDTO) -> Task | Reminder | Memory:
    if isinstance(item, TaskDTO):
        return task_dto_to_type(task=item)
    if isinstance(item, ReminderDTO):
        return reminder_dto_to_type(reminder=item)
    return memory_dto_to_type(memory=item)
