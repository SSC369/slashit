"""Implements capture's AnalyticsPort against the analytics domain."""

from uuid import UUID

from app.domains.analytics.public import (
    RecordEventInputDTO,
    RecordEventInteractor,
)


class CaptureAnalyticsAdapter:
    def __init__(self, *, record_event_interactor: RecordEventInteractor) -> None:
        self.record_event_interactor = record_event_interactor

    async def record_no_command_input(self, *, user_id: UUID) -> None:
        await self.record_event_interactor.record_event(
            dto=RecordEventInputDTO(user_id=user_id, event_type="no_command_input")
        )
