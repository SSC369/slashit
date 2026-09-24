"""Notifications' Procrastinate tasks. Thin: resolve collaborators, call one
interactor. See backend/.claude/rules/repo-rules.md section 14."""

from functools import lru_cache
from uuid import UUID

import structlog
from procrastinate import RetryStrategy
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.db import create_engine, create_session_factory
from app.core.deps import (
    build_purge_old_notifications_interactor,
    build_send_email_interactor,
)
from app.core.jobs import procrastinate_app
from app.core.settings import get_settings
from app.domains.notifications.constants import SEND_EMAIL_MAX_ATTEMPTS

logger = structlog.get_logger(__name__)


@lru_cache
def _session_factory() -> async_sessionmaker[AsyncSession]:
    return create_session_factory(create_engine(get_settings()))


@procrastinate_app.task(
    name="notifications.send_email",
    retry=RetryStrategy(max_attempts=SEND_EMAIL_MAX_ATTEMPTS, exponential_wait=5),
)
async def send_email(delivery_id: str) -> None:
    """Send one reminder email. Safe to repeat: a sent delivery is skipped,
    and the delivery id is Resend's idempotency key (AD-3)."""
    async with _session_factory()() as session:
        await build_send_email_interactor(session).send_email(
            delivery_id=UUID(delivery_id)
        )


@procrastinate_app.periodic(cron="15 3 * * *")  # daily, 03:15 UTC (FR-40)
@procrastinate_app.task(name="notifications.purge_old")
async def purge_old(timestamp: int) -> None:
    """Take notifications older than 90 days out of the list."""
    async with _session_factory()() as session:
        purged_count = await build_purge_old_notifications_interactor(
            session
        ).purge_old_notifications()
    logger.info("notifications.purged", purged_count=purged_count)
