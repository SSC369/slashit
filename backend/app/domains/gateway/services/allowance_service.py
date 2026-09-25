"""Is this user permitted another model call.

Requirement FR-8: the check runs before the provider is called, never after, so
a user over their limit costs nothing.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.domains.gateway.constants import (
    DEFAULT_REQUESTS_PER_DAY,
    LIMIT_WINDOW_HOURS,
)
from app.domains.gateway.interfaces.dtos import AllowanceDTO
from app.domains.gateway.interfaces.repositories import UsageRepository


class AllowanceService:
    def __init__(self, usage_repository: UsageRepository) -> None:
        self.usage_repository = usage_repository

    async def allowance_for(
        self, *, user_id: UUID, now: datetime | None = None
    ) -> AllowanceDTO:
        """How much headroom this user has left in the window.

        A user with no ``ai_user_limit`` row falls back to the default rather
        than to unlimited. Failing open on a spend control is the wrong failure.
        """
        now = now or datetime.now(UTC)
        window_start = now - timedelta(hours=LIMIT_WINDOW_HOURS)

        limit = await self.usage_repository.get_request_limit_for_user(user_id=user_id)
        if limit is None:
            limit = DEFAULT_REQUESTS_PER_DAY

        # Tech stack T9: embeddings are recorded but never counted.
        used = await self.usage_repository.count_since(
            user_id=user_id, since=window_start, operation="generate"
        )

        return AllowanceDTO(
            limit=limit,
            used=used,
            resets_at=now + timedelta(hours=LIMIT_WINDOW_HOURS),
        )
