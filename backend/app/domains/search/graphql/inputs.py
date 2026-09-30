"""Strawberry input types for search."""

from enum import Enum

import strawberry


@strawberry.enum
class SearchEventKind(Enum):
    SEARCH_RESULT_OPENED = "search_result_opened"
    ANSWER_CITATION_OPENED = "answer_citation_opened"
    RELATED_OPENED = "related_opened"


@strawberry.input
class RecordSearchEventInput:
    kind: SearchEventKind
    # 1-based: a row's place down the list, or a citation's number.
    position: int
