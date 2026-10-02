"""Implements records' EventRecordsPort against the events domain."""

from uuid import UUID

from app.domains.events.public import EventDTO, EventService


class EventRecordsAdapter:
    def __init__(self, *, event_service: EventService) -> None:
        self.event_service = event_service

    async def list_events(self, *, user_id: UUID) -> list[EventDTO]:
        return await self.event_service.list_for_records(user_id=user_id)
