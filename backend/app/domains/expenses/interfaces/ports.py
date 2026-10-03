"""What expenses needs from other domains, in its own words.

Per repo-rules.md section 6, the port belongs to the consumer.
"""

from datetime import date
from typing import Literal, Protocol
from uuid import UUID

ExpenseEventType = Literal[
    "expense_saved",
    "expense_amount_edited",
    "expense_category_edited",
    "expense_deleted",
]


class LocalDatePort(Protocol):
    """The user's local today, so a period reads in their zone (AD-3)."""

    async def local_today(self, *, user_id: UUID) -> date: ...


class ExpenseAnalyticsPort(Protocol):
    """PRD section 8's events. Ids and kinds only, never a description or an
    amount (NFR-7, AD-9)."""

    async def record_expense_event(
        self, *, user_id: UUID, event_type: ExpenseEventType
    ) -> None: ...

    async def record_summary_viewed(self, *, user_id: UUID, from_command: bool) -> None:
        """PRD §8's summaries metric. ``from_command`` tells ``/expenses`` from
        the Records band. Never a total."""
        ...


class ExpenseEmbeddingPort(Protocol):
    """The meaning of a description, stored as a document (005 D-22). None on
    any gateway failure: the embed job then retries."""

    async def embed_expense_description(
        self, *, user_id: UUID, description: str
    ) -> tuple[float, ...] | None: ...


class ExpenseEmbedQueue(Protocol):
    """Queues one expense's embed off the request path (sub-plan 4.3). Never
    fails the save that called it."""

    async def queue_expense_embed(
        self, *, user_id: UUID, expense_id: UUID, delay_seconds: int
    ) -> None: ...
