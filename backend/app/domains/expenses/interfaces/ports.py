"""What expenses needs from other domains, in its own words.

Per repo-rules.md section 6, the port belongs to the consumer.
"""

from typing import Literal, Protocol
from uuid import UUID

ExpenseEventType = Literal[
    "expense_saved",
    "expense_amount_edited",
    "expense_category_edited",
    "expense_deleted",
]


class ExpenseAnalyticsPort(Protocol):
    """PRD section 8's events. Ids and kinds only, never a description or an
    amount (NFR-7, AD-9)."""

    async def record_expense_event(
        self, *, user_id: UUID, event_type: ExpenseEventType
    ) -> None: ...
