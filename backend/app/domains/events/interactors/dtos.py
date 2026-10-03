"""Input DTOs, one per use case."""

from dataclasses import dataclass
from uuid import UUID

from app.domains.events.interfaces.dtos import (
    EventEdit,
    EventFields,
    RecordOriginValue,
)


@dataclass(frozen=True)
class CreateEventInputDTO:
    user_id: UUID
    fields: EventFields
    origin: RecordOriginValue
    original_input: str | None


@dataclass(frozen=True)
class GetEventInputDTO:
    user_id: UUID
    event_id: UUID


@dataclass(frozen=True)
class ListEventsInputDTO:
    user_id: UUID


@dataclass(frozen=True)
class UpdateEventInputDTO:
    user_id: UUID
    event_id: UUID
    edit: EventEdit


@dataclass(frozen=True)
class DeleteEventInputDTO:
    user_id: UUID
    event_id: UUID
