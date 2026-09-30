"""The records view's search, one page at a time (FR-22 to FR-24)."""

from app.domains.search.constants import MAX_SEARCH_LENGTH, PAGE_LIMIT_MAX
from app.domains.search.graphql.errors import SearchTooLongError
from app.domains.search.interactors.dtos import SearchRecordsInputDTO
from app.domains.search.interfaces.dtos import SearchPageDTO
from app.domains.search.services.search_service import SearchService


class SearchRecordsInteractor:
    def __init__(self, *, search_service: SearchService) -> None:
        self.search_service = search_service

    async def search_records(self, *, dto: SearchRecordsInputDTO) -> SearchPageDTO:
        """Ranked as `/search` ranks, filtered to a type when one is chosen.

        Raises:
            SearchTooLongError: the text is over the length a search allows.
            ValueError: empty text, or an offset or limit out of range. The
                records view never sends either, so each is a client bug.
        """
        text = dto.text.strip()
        self._validate_text(text=text)
        self._validate_page(offset=dto.offset, limit=dto.limit)
        return await self.search_service.search_page(
            user_id=dto.user_id,
            text=text,
            record_type=dto.record_type,
            offset=dto.offset,
            limit=dto.limit,
        )

    def _validate_text(self, *, text: str) -> None:
        if not text:
            raise ValueError("a search needs text")
        if len(text) > MAX_SEARCH_LENGTH:
            raise SearchTooLongError(length=len(text))

    def _validate_page(self, *, offset: int, limit: int) -> None:
        if offset < 0:
            raise ValueError("offset starts at 0")
        if not 1 <= limit <= PAGE_LIMIT_MAX:
            raise ValueError(f"limit is 1 to {PAGE_LIMIT_MAX}")
