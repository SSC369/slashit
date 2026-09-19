"""Data crossing analytics' own boundaries. Frozen, never a model instance."""

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

EventType = Literal["no_command_input", "records_view_opened"]


@dataclass(frozen=True)
class RecordEventInputDTO:
    user_id: UUID
    event_type: EventType
