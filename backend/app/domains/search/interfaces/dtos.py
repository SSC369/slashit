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

from app.domains.events.public import Event, EventDTO, event_dto_to_type
from app.domains.expenses.public import Expense, ExpenseDTO, expense_dto_to_type
from app.domains.memories.public import Memory, MemoryDTO, memory_dto_to_type
from app.domains.records.public import Task, TaskDTO, task_dto_to_type
from app.domains.reminders.public import Reminder, ReminderDTO, reminder_dto_to_type
from app.domains.search.constants import MAX_SEARCH_LENGTH

RecordDTO = TaskDTO | ReminderDTO | MemoryDTO | ExpenseDTO | EventDTO


@strawberry.enum
class RecordType(StrEnum):
    TASK = "task"
    REMINDER = "reminder"
    MEMORY = "memory"
    # 006 sub-plan 4.3: expenses are searchable from the day they ship (FR-29).
    EXPENSE = "expense"
    # Epic 007 FR-30: events, sub-plan 4.2.
    EVENT = "event"


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
    # The [n] the written answer cites this record as; None when uncited.
    citation: int | None


@dataclass(frozen=True)
class SearchGroupDTO:
    record_type: RecordType
    hits: list[SearchHitDTO]
    total: int


@dataclass(frozen=True)
class AnswerSentenceDTO:
    """FR-17: every sentence cites at least one record, as 1 to n."""

    text: str
    citations: list[int]


@dataclass(frozen=True)
class SearchAnswerDTO:
    sentences: list[AnswerSentenceDTO]


@dataclass(frozen=True)
class AnswerRecordDTO:
    """One ranked record as the model sees it (FR-16): a number, never an id."""

    number: int
    record_type: RecordType
    text: str
    detail: str


@dataclass(frozen=True)
class AnswerDraftDTO:
    """What the model returned, before AD-5's check."""

    sentences: list[tuple[str, list[int]]]
    supported: bool


@dataclass(frozen=True)
class AnswerRefusedDTO:
    """No answer could be written (FR-19). `limit_reached` when the refusal was
    the user's daily allowance rather than the model, so the card can say so."""

    limit_reached: bool


@dataclass(frozen=True)
class SearchResultsDTO:
    """FR-7: groups ordered by each group's best hit; empty when nothing
    matched (FR-10). Slice 2: a question adds the checked answer, or says no
    record supports one (FR-18), or that none could be written (FR-19)."""

    query: str
    groups: list[SearchGroupDTO]
    meaning_unavailable: bool
    answer: SearchAnswerDTO | None = None
    no_support: bool = False
    answer_unavailable: bool = False
    answer_limit_reached: bool = False


@dataclass(frozen=True)
class SearchTooLongDTO:
    """FR-3: nothing was searched; the client keeps the text."""

    length: int
    limit: int = MAX_SEARCH_LENGTH


@dataclass(frozen=True)
class SearchPageDTO:
    """One page of the records view's search (FR-22). Never an answer."""

    query: str
    hits: list[SearchHitDTO]
    # Matches in the chosen type, or in every type when none is chosen.
    total: int
    # Matches outside the chosen type, for "9 other records match"; 0 with none.
    other_types_total: int
    meaning_unavailable: bool


@dataclass(frozen=True)
class RelatedRecordDTO:
    """FR-25: one record close in meaning to the one on screen."""

    record_type: RecordType
    item: RecordDTO


SearchRecord = Annotated[
    Task | Reminder | Memory | Expense | Event, strawberry.union("SearchRecord")
]


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
class AnswerSentence:
    text: str
    citations: list[int]


@strawberry.type
class SearchAnswer:
    sentences: list[AnswerSentence]


@strawberry.type
class SearchResults:
    query: str
    groups: list[SearchGroup]
    meaning_unavailable: bool
    answer: SearchAnswer | None
    no_support: bool
    answer_unavailable: bool
    answer_limit_reached: bool


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
        answer=(
            None
            if results.answer is None
            else SearchAnswer(
                sentences=[
                    AnswerSentence(text=sentence.text, citations=sentence.citations)
                    for sentence in results.answer.sentences
                ]
            )
        ),
        no_support=results.no_support,
        answer_unavailable=results.answer_unavailable,
        answer_limit_reached=results.answer_limit_reached,
    )


@strawberry.type
class SearchPage:
    query: str
    hits: list[SearchRecord]
    total: int
    other_types_total: int
    meaning_unavailable: bool


def search_page_to_type(*, page: SearchPageDTO) -> SearchPage:
    return SearchPage(
        query=page.query,
        hits=[_record_to_type(item=hit.item) for hit in page.hits],
        total=page.total,
        other_types_total=page.other_types_total,
        meaning_unavailable=page.meaning_unavailable,
    )


def related_records_to_type(*, related: list[RelatedRecordDTO]) -> list[SearchRecord]:
    return [_record_to_type(item=record.item) for record in related]


def search_too_long_to_type(*, too_long: SearchTooLongDTO) -> SearchTooLong:
    return SearchTooLong(length=too_long.length, limit=too_long.limit)


def _record_to_type(*, item: RecordDTO) -> Task | Reminder | Memory | Expense | Event:
    if isinstance(item, TaskDTO):
        return task_dto_to_type(task=item)
    if isinstance(item, ReminderDTO):
        return reminder_dto_to_type(reminder=item)
    if isinstance(item, ExpenseDTO):
        return expense_dto_to_type(expense=item)
    if isinstance(item, EventDTO):
        return event_dto_to_type(event=item)
    return memory_dto_to_type(memory=item)
