"""Record that a search result, a citation or a related record was opened
(PRD section 8)."""

from app.domains.search.interactors.dtos import RecordSearchEventInputDTO
from app.domains.search.interfaces.ports import SearchAnalyticsPort

# The property each kind stores its position under.
_POSITION_KEY = {
    "search_result_opened": "position",
    "answer_citation_opened": "citation",
    "related_opened": "position",
}


class RecordSearchEventInteractor:
    def __init__(self, *, analytics: SearchAnalyticsPort) -> None:
        self.analytics = analytics

    async def record_search_event(self, *, dto: RecordSearchEventInputDTO) -> None:
        """Numbers only, never text (AD-10).

        Raises:
            ValueError: a position under 1. A client bug, not an outcome.
        """
        self._validate_position(position=dto.position)
        await self.analytics.record_search_event(
            user_id=dto.user_id,
            event_type=dto.kind,
            properties={_POSITION_KEY[dto.kind]: dto.position},
        )

    def _validate_position(self, *, position: int) -> None:
        if position < 1:
            raise ValueError("position starts at 1")
