"""Implements search's SearchAnalyticsPort against the analytics domain."""

from uuid import UUID

from app.domains.analytics.public import RecordEventInputDTO, RecordEventInteractor


class SearchAnalyticsAdapter:
    def __init__(self, *, record_event_interactor: RecordEventInteractor) -> None:
        self.record_event_interactor = record_event_interactor

    async def record_search_run(self, *, user_id: UUID) -> None:
        await self.record_event_interactor.record_event(
            dto=RecordEventInputDTO(user_id=user_id, event_type="search_run")
        )
