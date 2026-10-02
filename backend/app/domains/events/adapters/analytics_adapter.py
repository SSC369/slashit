"""Implements events' EventAnalyticsPort against the analytics domain."""

from uuid import UUID

from app.domains.analytics.public import RecordEventInputDTO, RecordEventInteractor


class EventAnalyticsAdapter:
    def __init__(self, *, record_event_interactor: RecordEventInteractor) -> None:
        self.record_event_interactor = record_event_interactor

    async def record_event_created(
        self, *, user_id: UUID, field_presence: dict[str, bool]
    ) -> None:
        await self.record_event_interactor.record_event(
            dto=RecordEventInputDTO(
                user_id=user_id,
                event_type="event_created",
                properties=dict(field_presence),
            )
        )
