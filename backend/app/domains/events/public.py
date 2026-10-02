"""The only names other domains may import from events.

A domain's public surface is its contract. Adding a name here is a deliberate
act, reviewed like an API change. See backend/.claude/rules/repo-rules.md
section 6.
"""

from app.domains.events.interfaces.dtos import (
    AlertChoiceDTO,
    Event,
    EventDTO,
    EventFields,
    EventLimitReached,
    EventNeedsAlertChoice,
    EventNeedsDate,
    event_dto_to_type,
)
from app.domains.events.services.event_service import EventService

__all__ = [
    "AlertChoiceDTO",
    "Event",
    "EventDTO",
    "EventFields",
    "EventLimitReached",
    "EventNeedsAlertChoice",
    "EventNeedsDate",
    "EventService",
    "event_dto_to_type",
]
