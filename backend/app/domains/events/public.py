"""The only names other domains may import from events.

A domain's public surface is its contract. Adding a name here is a deliberate
act, reviewed like an API change. See backend/.claude/rules/repo-rules.md
section 6.
"""

from app.domains.events.interfaces.dtos import (
    AlertNotSetDTO,
    Event,
    EventAlertNotSet,
    EventDTO,
    EventFields,
    EventLimitReached,
    EventNeedsDate,
    alert_not_set_to_type,
    event_dto_to_type,
)
from app.domains.events.services.event_service import EventService

__all__ = [
    "AlertNotSetDTO",
    "Event",
    "EventAlertNotSet",
    "EventDTO",
    "EventFields",
    "EventLimitReached",
    "EventNeedsDate",
    "EventService",
    "alert_not_set_to_type",
    "event_dto_to_type",
]
