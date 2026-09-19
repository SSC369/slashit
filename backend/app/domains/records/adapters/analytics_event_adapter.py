"""Implements records' AnalyticsPort against the analytics domain."""

from uuid import UUID

from app.domains.analytics.public import (
    RecordEventInputDTO,
    RecordEventInteractor,
)


class RecordsAnalyticsAdapter:
    def __init__(self, *, record_event_interactor: RecordEventInteractor) -> None:
        self.record_event_interactor = record_event_interactor

    async def record_records_view_opened(self, *, user_id: UUID) -> None:
        await self.record_event_interactor.record_event(
            dto=RecordEventInputDTO(
                user_id=user_id, event_type="records_view_opened"
            )
        )
