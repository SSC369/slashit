"""What events needs from other domains, in its own words.

Per repo-rules.md section 6, the port belongs to the consumer.
"""

from typing import Protocol
from uuid import UUID

from app.domains.events.interfaces.dtos import UserClockDTO


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
