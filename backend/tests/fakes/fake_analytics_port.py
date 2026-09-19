"""An in-memory analytics port. Not a mock: it behaves, so tests read as
behaviour. Satisfies both capture's and records' AnalyticsPort Protocols
structurally, since each names only the one method its domain needs."""

import uuid


class FakeAnalyticsPort:
    def __init__(self) -> None:
        self.no_command_input_calls: list[uuid.UUID] = []
        self.records_view_opened_calls: list[uuid.UUID] = []

    async def record_no_command_input(self, *, user_id: uuid.UUID) -> None:
        self.no_command_input_calls.append(user_id)

    async def record_records_view_opened(self, *, user_id: uuid.UUID) -> None:
        self.records_view_opened_calls.append(user_id)
