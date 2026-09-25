"""Data crossing analytics' own boundaries. Frozen, never a model instance."""

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

EventType = Literal[
    "no_command_input",
    "records_view_opened",
    # Epic 004, migration 0027.
    "memory_saved",
    "memory_lookup",
    "memory_conflict_answered",
    "memory_forgotten",
    "memory_category_edited",
    "memory_secret_caution",
]


@dataclass(frozen=True)
class RecordEventInputDTO:
    user_id: UUID
    event_type: EventType
