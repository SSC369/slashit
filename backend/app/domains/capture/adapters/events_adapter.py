"""Implements capture's EventPort against the events domain."""

from uuid import UUID

from app.domains.events.public import (
    EventDTO,
    EventFields,
    EventLimitReached,
    EventNeedsAlertChoice,
    EventNeedsDate,
    EventService,
)


class EventsAdapter:
    def __init__(self, *, event_service: EventService) -> None:
        self.event_service = event_service

    async def create_event(
        self, *, user_id: UUID, fields: EventFields, original_input: str
    ) -> EventDTO | EventLimitReached | EventNeedsDate | EventNeedsAlertChoice:
        return await self.event_service.create_event(
            user_id=user_id,
            fields=fields,
            origin="command",
            original_input=original_input,
        )

    async def list_upcoming(self, *, user_id: UUID) -> list[EventDTO]:
        return await self.event_service.list_upcoming(user_id=user_id)
