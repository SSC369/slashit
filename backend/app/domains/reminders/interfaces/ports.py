"""What reminders needs from other domains, in its own words.

Per repo-rules.md section 6, the port belongs to the consumer. It names the
one thing reminders needs and not the domain that supplies it.
"""

from typing import Protocol
from uuid import UUID

from app.domains.reminders.interfaces.dtos import UserClockDTO


class UserClockPort(Protocol):
    """Where the user is, and the time a date-only reminder takes (FR-3)."""

    async def get_user_clock(self, *, user_id: UUID) -> UserClockDTO: ...
