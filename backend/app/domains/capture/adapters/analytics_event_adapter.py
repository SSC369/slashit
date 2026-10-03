"""Implements capture's AnalyticsPort against the analytics domain."""

from uuid import UUID

from app.domains.analytics.public import (
    RecordEventInputDTO,
    RecordEventInteractor,
)
from app.domains.capture.interfaces.ports import ExpenseCaptureEventType


class CaptureAnalyticsAdapter:
    def __init__(self, *, record_event_interactor: RecordEventInteractor) -> None:
        self.record_event_interactor = record_event_interactor

    async def record_no_command_input(self, *, user_id: UUID) -> None:
        await self.record_event_interactor.record_event(
            dto=RecordEventInputDTO(user_id=user_id, event_type="no_command_input")
        )

    async def record_expense_capture_event(
        self, *, user_id: UUID, event_type: ExpenseCaptureEventType, is_choice: bool
    ) -> None:
        await self.record_event_interactor.record_event(
            dto=RecordEventInputDTO(
                user_id=user_id,
                event_type=event_type,
                properties={"is_choice": is_choice},
            )
        )
