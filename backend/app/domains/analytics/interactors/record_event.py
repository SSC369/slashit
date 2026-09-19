from app.domains.analytics.interfaces.dtos import RecordEventInputDTO
from app.domains.analytics.interfaces.repositories import EventRepository


class RecordEventInteractor:
    def __init__(self, *, event_repository: EventRepository) -> None:
        self.event_repository = event_repository

    async def record_event(self, *, dto: RecordEventInputDTO) -> None:
        """Record one instrumentation event. No business rule to enforce:
        every caller-supplied event type is valid by construction, since
        EventType is a closed Literal."""
        await self.event_repository.record_event(
            user_id=dto.user_id, event_type=dto.event_type
        )
