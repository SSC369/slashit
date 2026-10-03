"""Expenses' Procrastinate tasks. Thin: resolve collaborators, call one
interactor. See backend/.claude/rules/repo-rules.md section 14.

Both run on the service-role connection, as a background job may (T3). The
backfill reads every user's rows; each embed then writes inside a
``user_transaction`` for its own user, so Row Level Security still binds.
"""

from functools import lru_cache
from uuid import UUID

import structlog
from procrastinate import RetryStrategy
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.db import create_engine, create_session_factory
from app.core.deps import (
    build_embed_expense_interactor,
    build_queue_missing_expense_embeddings_interactor,
)
from app.core.jobs import procrastinate_app
from app.core.settings import get_settings
from app.domains.expenses.constants import EMBED_MAX_ATTEMPTS
from app.domains.expenses.interactors.dtos import (
    EmbedExpenseInputDTO,
    QueueMissingExpenseEmbeddingsInputDTO,
)

logger = structlog.get_logger(__name__)


@lru_cache
def _session_factory() -> async_sessionmaker[AsyncSession]:
    return create_session_factory(create_engine(get_settings()))


@procrastinate_app.task(
    name="expenses.embed_expense",
    retry=RetryStrategy(max_attempts=EMBED_MAX_ATTEMPTS, exponential_wait=2),
)
async def embed_expense(user_id: str, expense_id: str) -> None:
    """Give one expense its meaning vector (sub-plan 4.3). Safe to run twice."""
    session_factory = _session_factory()
    async with session_factory() as session:
        interactor = build_embed_expense_interactor(
            session=session, session_factory=session_factory
        )
        embedded = await interactor.embed_expense(
            dto=EmbedExpenseInputDTO(user_id=UUID(user_id), expense_id=UUID(expense_id))
        )
    logger.info("expenses.embed_expense", expense_id=expense_id, embedded=embedded)


@procrastinate_app.periodic(cron="*/10 * * * *")  # every 10 minutes, as 004 P-6
@procrastinate_app.task(name="expenses.backfill_embeddings")
async def backfill_embeddings(timestamp: int, full: bool = False) -> None:
    """Queue a vector for expenses with none. ``full`` is deferred once, by
    hand, at deploy (T-3.9); the periodic run covers recent ones only."""
    async with _session_factory()() as session:
        queued_count = await build_queue_missing_expense_embeddings_interactor(
            session
        ).queue_missing_expense_embeddings(
            dto=QueueMissingExpenseEmbeddingsInputDTO(full=full)
        )
    logger.info("expenses.backfill_embeddings", queued_count=queued_count, full=full)
