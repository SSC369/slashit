"""Reminders' Procrastinate tasks. Thin: resolve collaborators, call one
interactor. See backend/.claude/rules/repo-rules.md section 14.

Both run on the service-role connection, as a background job may (T3). The
sweep reads every user's due rows; each firing then writes inside a
``user_transaction`` for its own user, so Row Level Security still binds.
"""

from datetime import datetime
from functools import lru_cache
from uuid import UUID

import structlog
from procrastinate import RetryStrategy
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.db import create_engine, create_session_factory
from app.core.deps import (
    build_embed_reminder_interactor,
    build_fire_due_interactor,
    build_fire_one_interactor,
    build_queue_missing_reminder_embeddings_interactor,
    build_reconcile_reminders_interactor,
    build_rezone_reminders_interactor,
)
from app.core.jobs import procrastinate_app
from app.core.settings import get_settings
from app.domains.reminders.constants import (
    EMBED_MAX_ATTEMPTS,
    FIRE_ONE_MAX_ATTEMPTS,
    REZONE_MAX_ATTEMPTS,
)
from app.domains.reminders.interactors.dtos import (
    EmbedReminderInputDTO,
    QueueMissingReminderEmbeddingsInputDTO,
)

logger = structlog.get_logger(__name__)


@lru_cache
def _session_factory() -> async_sessionmaker[AsyncSession]:
    return create_session_factory(create_engine(get_settings()))


@procrastinate_app.periodic(cron="* * * * *")  # every minute (AD-2)
@procrastinate_app.task(name="reminders.fire_due")
async def fire_due(timestamp: int) -> None:
    """Queue one `fire_one` per due occurrence. Fires nothing itself."""
    async with _session_factory()() as session:
        queued_count = await build_fire_due_interactor(session).fire_due()
    logger.info("reminders.fire_due", queued_count=queued_count)


@procrastinate_app.task(
    name="reminders.fire_one",
    retry=RetryStrategy(max_attempts=FIRE_ONE_MAX_ATTEMPTS, exponential_wait=2),
)
async def fire_one(reminder_id: str, scheduled_for: str) -> None:
    """Fire one occurrence. Safe to run twice (AD-3)."""
    async with _session_factory()() as session:
        await build_fire_one_interactor(session).fire_one(
            reminder_id=UUID(reminder_id),
            scheduled_for=datetime.fromisoformat(scheduled_for),
        )


@procrastinate_app.task(
    name="reminders.timezone_changed",
    retry=RetryStrategy(max_attempts=REZONE_MAX_ATTEMPTS, exponential_wait=2),
)
async def timezone_changed(user_id: str) -> None:
    """Move one user's reminders to their new zone (AD-6). Deferred by
    identity by name; safe to repeat, since a moved reminder is skipped."""
    async with _session_factory()() as session:
        moved_count = await build_rezone_reminders_interactor(session).rezone_reminders(
            user_id=UUID(user_id)
        )
    logger.info("reminders.rezoned", user_id=user_id, moved_count=moved_count)


@procrastinate_app.periodic(cron="30 * * * *")  # hourly, at minute 30 (NFR-4)
@procrastinate_app.task(name="reminders.reconcile")
async def reconcile(timestamp: int) -> None:
    """Log every reminder overdue with no firing. Repairs nothing."""
    async with _session_factory()() as session:
        lost_count = await build_reconcile_reminders_interactor(session).reconcile()
    logger.info("reminders.reconcile", lost_count=lost_count)


@procrastinate_app.task(
    name="reminders.embed_reminder",
    retry=RetryStrategy(max_attempts=EMBED_MAX_ATTEMPTS, exponential_wait=2),
)
async def embed_reminder(user_id: str, reminder_id: str) -> None:
    """Give one reminder its meaning vector (005 AD-7). Safe to run twice.
    Runs inside a ``user_transaction`` for the reminder's own user."""
    session_factory = _session_factory()
    async with session_factory() as session:
        interactor = build_embed_reminder_interactor(
            session=session, session_factory=session_factory
        )
        embedded = await interactor.embed_reminder(
            dto=EmbedReminderInputDTO(
                user_id=UUID(user_id), reminder_id=UUID(reminder_id)
            )
        )
    logger.info("reminders.embed_reminder", reminder_id=reminder_id, embedded=embedded)


@procrastinate_app.periodic(cron="*/10 * * * *")  # every 10 minutes, as 004 P-6
@procrastinate_app.task(name="reminders.backfill_embeddings")
async def backfill_embeddings(timestamp: int, full: bool = False) -> None:
    """Queue a vector for reminders with none. ``full`` is deferred once, by
    hand, at deploy (index §6); the periodic run covers recent ones only."""
    async with _session_factory()() as session:
        queued_count = await build_queue_missing_reminder_embeddings_interactor(
            session
        ).queue_missing_reminder_embeddings(
            dto=QueueMissingReminderEmbeddingsInputDTO(full=full)
        )
    logger.info("reminders.backfill_embeddings", queued_count=queued_count, full=full)
