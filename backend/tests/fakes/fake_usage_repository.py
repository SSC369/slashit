"""In-memory UsageRepository. Not a mock: it behaves, so tests read as behaviour."""

from datetime import datetime
from uuid import UUID

from app.domains.gateway.interfaces.dtos import OperationValue, UsageRecord


class FakeUsageRepository:
    """Satisfies the UsageRepository Protocol without inheriting from it."""

    def __init__(self, limit: int | None = None, used: int = 0) -> None:
        self.records: list[UsageRecord] = []
        self._limit = limit
        self._used = used
        self.record_should_fail = False
        self.counted_operations: list[OperationValue] = []

    async def record(self, *, usage: UsageRecord, occurred_at: datetime) -> None:
        if self.record_should_fail:
            raise RuntimeError("simulated write failure")
        self.records.append(usage)

    async def count_since(
        self, *, user_id: UUID, since: datetime, operation: OperationValue
    ) -> int:
        self.counted_operations.append(operation)
        return self._used

    async def get_request_limit_for_user(self, *, user_id: UUID) -> int | None:
        return self._limit

    @property
    def outcomes(self) -> list[str]:
        return [r.outcome for r in self.records]
