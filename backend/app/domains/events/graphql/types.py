"""Events' mutation results. ``Event`` itself lives in ``interfaces/dtos.py``
so capture and records can carry it (repo-rules.md section 6.2)."""

import strawberry

from app.domains.events.interfaces.dtos import Event, EventAlertNotSet


@strawberry.type
class EventUpdated:
    """FR-28. FR-19 and FR-33: each alert asked for and not set, with why."""

    event: Event
    alerts_not_set: list[EventAlertNotSet]


@strawberry.type
class EventDeleted:
    """FR-29: the event, its yearly series and its alerts are gone."""

    id: strawberry.ID
