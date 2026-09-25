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
    build_fire_due_interactor,
    build_fire_one_interactor,
    build_reconcile_reminders_interactor,
    build_rezone_reminders_interactor,
)
from app.core.jobs import procrastinate_app
from app.core.settings import get_settings
from app.domains.reminders.constants import (
    FIRE_ONE_MAX_ATTEMPTS,
    REZONE_MAX_ATTEMPTS,
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
