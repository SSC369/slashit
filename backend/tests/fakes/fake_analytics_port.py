"""An in-memory analytics port. Not a mock: it behaves, so tests read as
behaviour. Satisfies both capture's and records' AnalyticsPort Protocols
structurally, since each names only the one method its domain needs."""

import uuid

from app.domains.capture.interfaces.ports import ExpenseCaptureEventType


class FakeAnalyticsPort:
    def __init__(self) -> None:
        self.no_command_input_calls: list[uuid.UUID] = []
        self.records_view_opened_calls: list[uuid.UUID] = []
        self.expense_capture_events: list[tuple[ExpenseCaptureEventType, bool]] = []

    async def record_no_command_input(self, *, user_id: uuid.UUID) -> None:
        self.no_command_input_calls.append(user_id)

    async def record_records_view_opened(self, *, user_id: uuid.UUID) -> None:
        self.records_view_opened_calls.append(user_id)

    async def record_expense_capture_event(
        self,
        *,
        user_id: uuid.UUID,
        event_type: ExpenseCaptureEventType,
        is_choice: bool,
    ) -> None:
        self.expense_capture_events.append((event_type, is_choice))
