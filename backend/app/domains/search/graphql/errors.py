"""Search's one failure outcome for its queries, as an exception.

Its union member, ``SearchTooLong``, lives in ``interfaces/dtos.py`` because
capture carries it too (repo-rules.md section 6.2); the exception sits here,
per sections 7.1 and 8.
"""

from app.core.errors import DomainError
from app.domains.search.constants import MAX_SEARCH_LENGTH
from app.domains.search.interfaces.dtos import SearchTooLong


class SearchTooLongError(DomainError):
    gql_type = SearchTooLong

    def __init__(self, *, length: int) -> None:
        self.length = length
        self.limit = MAX_SEARCH_LENGTH
        super().__init__(f"A search is at most {MAX_SEARCH_LENGTH} characters")
