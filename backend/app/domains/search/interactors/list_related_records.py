"""The records close in meaning to the one whose detail is open (FR-25)."""

from app.domains.search.interactors.dtos import ListRelatedRecordsInputDTO
from app.domains.search.interfaces.dtos import RelatedRecordDTO
from app.domains.search.services.search_service import SearchService


class ListRelatedRecordsInteractor:
    def __init__(self, *, search_service: SearchService) -> None:
        self.search_service = search_service

    async def list_related_records(
        self, *, dto: ListRelatedRecordsInputDTO
    ) -> list[RelatedRecordDTO]:
        """Worked out on every call and never stored (FR-27). A record the
        user cannot see has none, so another account's id reveals nothing."""
        return await self.search_service.related(
            user_id=dto.user_id, record_type=dto.record_type, record_id=dto.record_id
        )
