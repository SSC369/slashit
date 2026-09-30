"""The only names other domains may import from search.

A domain's public surface is its contract. Adding a name here is a deliberate
act, reviewed like an API change. See backend/.claude/rules/repo-rules.md
section 6.
"""

from app.domains.search.constants import MAX_SEARCH_LENGTH
from app.domains.search.interfaces.dtos import (
    RecordType,
    SearchResults,
    SearchResultsDTO,
    SearchTooLong,
    SearchTooLongDTO,
    search_results_to_type,
    search_too_long_to_type,
)
from app.domains.search.services.search_service import SearchService

__all__ = [
    "MAX_SEARCH_LENGTH",
    "RecordType",
    "SearchResults",
    "SearchResultsDTO",
    "SearchService",
    "SearchTooLong",
    "SearchTooLongDTO",
    "search_results_to_type",
    "search_too_long_to_type",
]
