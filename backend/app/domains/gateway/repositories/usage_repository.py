"""The only SQL in the gateway domain. Returns DTOs, never models."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.db import user_transaction
from app.domains.gateway.interfaces.dtos import OperationValue, UsageRecord
from app.domains.gateway.models import AiUsage, AiUserLimit


class SqlUsageRepository:
    """Reads and writes ai_usage and ai_user_limit.

    Takes a session factory rather than a session, because the usage write opens
    its own transaction. Decision AD-8, amended 2026-09-12: a provider call that
    happened must be recorded whether or not the caller's later work succeeds.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def record(self, *, usage: UsageRecord, occurred_at: datetime) -> None:
        """Write one row and commit it, in its own transaction."""
        async with (
            self.session_factory() as session,
            user_transaction(session, usage.user_id) as scoped,
        ):
            scoped.add(
                AiUsage(
                    id=usage.id,
                    user_id=usage.user_id,
                    provider=usage.provider,
                    model=usage.model,
                    input_tokens=usage.input_tokens,
                    output_tokens=usage.output_tokens,
                    total_tokens=usage.total_tokens,
                    outcome=usage.outcome,
                    latency_ms=usage.latency_ms,
                    operation=usage.operation,
                    created_at=occurred_at,
                )
            )

    async def count_since(
        self, *, user_id: UUID, since: datetime, operation: OperationValue
    ) -> int:
        async with (
            self.session_factory() as session,
            user_transaction(session, user_id) as scoped,
        ):
            total = await scoped.scalar(
                select(func.count())
                .select_from(AiUsage)
                .where(
                    AiUsage.user_id == user_id,
                    AiUsage.created_at >= since,
                    AiUsage.operation == operation,
                )
            )
        return int(total or 0)

    async def get_request_limit_for_user(self, *, user_id: UUID) -> int | None:
        async with (
            self.session_factory() as session,
            user_transaction(session, user_id) as scoped,
        ):
            requests_per_day = await scoped.scalar(
                select(AiUserLimit.requests_per_day).where(
                    AiUserLimit.user_id == user_id
                )
            )
        return int(requests_per_day) if requests_per_day is not None else None
