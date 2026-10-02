"""An in-memory ExpenseAnalyticsPort that remembers each event type."""

import uuid

from app.domains.expenses.interfaces.ports import ExpenseEventType


class FakeExpenseAnalyticsPort:
    def __init__(self) -> None:
        self.events: list[ExpenseEventType] = []

    async def record_expense_event(
        self, *, user_id: uuid.UUID, event_type: ExpenseEventType
    ) -> None:
        self.events.append(event_type)
