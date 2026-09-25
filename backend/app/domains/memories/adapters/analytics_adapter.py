"""Implements memories' MemoryAnalyticsPort against the analytics domain."""

from uuid import UUID

from app.domains.analytics.public import RecordEventInputDTO, RecordEventInteractor
from app.domains.memories.interfaces.ports import MemoryEventType


class MemoryAnalyticsAdapter:
    def __init__(self, *, record_event_interactor: RecordEventInteractor) -> None:
        self.record_event_interactor = record_event_interactor

    async def record_memory_event(
        self, *, user_id: UUID, event_type: MemoryEventType
    ) -> None:
        await self.record_event_interactor.record_event(
            dto=RecordEventInputDTO(user_id=user_id, event_type=event_type)
        )
