"""Records' Procrastinate tasks. Thin: resolve collaborators, call one
interactor. See backend/.claude/rules/repo-rules.md section 14.

The embed job runs inside a ``user_transaction`` for the task's own user, so
Row Level Security binds the job as it binds a request. The backfill sweep
reads across users on the service-role connection (T3).
"""

from functools import lru_cache
from uuid import UUID

import structlog
from procrastinate import RetryStrategy
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.db import create_engine, create_session_factory
from app.core.deps import (
    build_embed_task_interactor,
    build_queue_missing_task_embeddings_interactor,
)
from app.core.jobs import procrastinate_app
from app.core.settings import get_settings
from app.domains.records.constants import EMBED_MAX_ATTEMPTS
from app.domains.records.interactors.dtos import (
    EmbedTaskInputDTO,
    QueueMissingTaskEmbeddingsInputDTO,
)

logger = structlog.get_logger(__name__)


@lru_cache
def _session_factory() -> async_sessionmaker[AsyncSession]:
    return create_session_factory(create_engine(get_settings()))


@procrastinate_app.task(
    name="records.embed_task",
    retry=RetryStrategy(max_attempts=EMBED_MAX_ATTEMPTS, exponential_wait=2),
)
async def embed_task(user_id: str, task_id: str) -> None:
    """Give one task its meaning vector (005 AD-7). Safe to run twice."""
    session_factory = _session_factory()
    async with session_factory() as session:
        interactor = build_embed_task_interactor(
            session=session, session_factory=session_factory
        )
        embedded = await interactor.embed_task(
            dto=EmbedTaskInputDTO(user_id=UUID(user_id), task_id=UUID(task_id))
        )
    logger.info("records.embed_task", task_id=task_id, embedded=embedded)


@procrastinate_app.periodic(cron="*/10 * * * *")  # every 10 minutes, as 004 P-6
@procrastinate_app.task(name="records.backfill_embeddings")
async def backfill_embeddings(timestamp: int, full: bool = False) -> None:
    """Queue a vector for tasks with none. ``full`` is deferred once, by hand,
    at deploy (index §6); the periodic run covers recent tasks only."""
    async with _session_factory()() as session:
        queued_count = await build_queue_missing_task_embeddings_interactor(
            session
        ).queue_missing_task_embeddings(
            dto=QueueMissingTaskEmbeddingsInputDTO(full=full)
        )
    logger.info("records.backfill_embeddings", queued_count=queued_count, full=full)
