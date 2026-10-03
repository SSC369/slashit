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
        self, *, user_id: UUID, field_presence: dict[str, bool], alert_count: int
    ) -> None: ...

    async def record_event_edited(
        self,
        *,
        user_id: UUID,
        minutes_since_created: int,
        changed_fields: dict[str, bool],
    ) -> None:
        """PRD §8 and G2: which parts an edit changed, and how soon after
        the event was made. Booleans and a count only (T6)."""
        ...

    async def record_alert_not_set(
        self, *, user_id: UUID, lead_minutes: int, is_over_cap: bool
    ) -> None:
        """FR-19 and FR-33, per alert: its lead, and whether the cap or a
        passed time stopped it."""
        ...


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


class EventEmbeddingPort(Protocol):
    """What events needs to give an event a meaning vector (005 AD-7). None
    when the model refused; the job then retries."""

    async def embed_event_text(
        self, *, user_id: UUID, text: str
    ) -> tuple[float, ...] | None: ...


class EventEmbedQueue(Protocol):
    """Queueing one event's embed job. Never fails the save that calls it."""

    async def queue_event_embed(
        self, *, user_id: UUID, event_id: UUID, delay_seconds: int
    ) -> None: ...
