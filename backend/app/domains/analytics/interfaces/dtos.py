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
    # Epic 005, migration 0035.
    "search_run",
    "search_result_opened",
    "answer_citation_opened",
    "related_opened",
    # Epic 007, migration 0038.
    "event_created",
]


# Epic 005: counts and positions, never text (T6, migration 0036's check).
EventProperties = dict[str, int | float | bool]


@dataclass(frozen=True)
class RecordEventInputDTO:
    user_id: UUID
    event_type: EventType
    properties: EventProperties | None = None
