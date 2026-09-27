"""Repository contracts. Protocols, so a fake needs no inheritance."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domains.gateway.interfaces.dtos import OperationValue, UsageRecord


class UsageRepository(Protocol):
    async def record(self, *, usage: UsageRecord, occurred_at: datetime) -> None:
        """Persist one call. Committed on its own, per decision AD-8."""
        ...

    async def count_since(
        self, *, user_id: UUID, since: datetime, operation: OperationValue
    ) -> int:
        """How many calls of this operation this user has made in the window."""
        ...

    async def get_request_limit_for_user(self, *, user_id: UUID) -> int | None:
        """The user's configured ceiling, or None when they have no row."""
        ...
