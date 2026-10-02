"""Implements expenses' ExpenseAnalyticsPort against the analytics domain."""

from uuid import UUID

from app.domains.analytics.public import RecordEventInputDTO, RecordEventInteractor
from app.domains.expenses.interfaces.ports import ExpenseEventType


class ExpenseAnalyticsAdapter:
    def __init__(self, *, record_event_interactor: RecordEventInteractor) -> None:
        self.record_event_interactor = record_event_interactor

    async def record_expense_event(
        self, *, user_id: UUID, event_type: ExpenseEventType
    ) -> None:
        await self.record_event_interactor.record_event(
            dto=RecordEventInputDTO(user_id=user_id, event_type=event_type)
        )
