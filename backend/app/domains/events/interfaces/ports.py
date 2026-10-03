"""What events needs from other domains, in its own words.

Per repo-rules.md section 6, the port belongs to the consumer.
"""

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domains.events.interfaces.dtos import (
    AlertNotSetDTO,
    EventAlertToSet,
    RecordOriginValue,
    UserClockDTO,
)


class UserClockPort(Protocol):
    """Where the user is, and the time an all-day event's alert counts back
    from (FR-15)."""

    async def get_user_clock(self, *, user_id: UUID) -> UserClockDTO: ...


class EventAnalyticsPort(Protocol):
    """PRD §8: which parts of an event's shape are used. Booleans only, never
    text (T6)."""

    async def record_event_created(
        self, *, user_id: UUID, field_presence: dict[str, bool]
    ) -> None: ...


class EventAlertsPort(Protocol):
    """Where an event's alerts are armed (build plan AD-3, AD-8)."""

    async def set_alerts(
        self,
        *,
        user_id: UUID,
        event_id: UUID,
        title: str,
        alerts: Sequence[EventAlertToSet],
        origin: RecordOriginValue,
        now: datetime,
    ) -> list[AlertNotSetDTO]:
        """Replace the event's alerts with ``alerts``; return those not set."""
        ...

    async def clear_alerts(self, *, user_id: UUID, event_id: UUID) -> None: ...
