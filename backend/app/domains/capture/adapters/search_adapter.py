"""Implements capture's SearchPort against the search domain (epic 005)."""

from uuid import UUID

from app.domains.search.public import SearchResultsDTO, SearchService


class SearchAdapter:
    def __init__(self, *, search_service: SearchService) -> None:
        self.search_service = search_service

    async def search(self, *, user_id: UUID, text: str) -> SearchResultsDTO:
        return await self.search_service.search_for_capture(user_id=user_id, text=text)
