"""What records needs from other domains, in its own words.

Per repo-rules.md section 6, the port belongs to the consumer.
"""

from typing import Protocol
from uuid import UUID

from app.domains.reminders.public import ReminderDTO


class AnalyticsPort(Protocol):
    """What records needs from analytics: log a records view being opened.
    That metric (PRD section 8) has no other data source."""

    async def record_records_view_opened(self, *, user_id: UUID) -> None: ...


class ReminderRecordsPort(Protocol):
    """What records needs from reminders: every live reminder, for the All
    tab (epic 003, FR-26). Records orders the merged list itself."""

    async def list_reminders(
        self, *, user_id: UUID, search: str | None
    ) -> list[ReminderDTO]: ...
