"""Events' Procrastinate tasks. Thin: resolve collaborators, call one
interactor. See backend/.claude/rules/repo-rules.md section 14.

All run on the service-role connection, as a background job may (T3). Each
event is then written inside a ``user_transaction`` for its own user, so Row
Level Security still binds.
"""

from functools import lru_cache
from uuid import UUID

import structlog
from procrastinate import RetryStrategy
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.db import create_engine, create_session_factory
from app.core.deps import (
    build_embed_event_interactor,
    build_queue_missing_event_embeddings_interactor,
    build_reconcile_event_alerts_interactor,
    build_rezone_events_interactor,
    build_roll_yearly_interactor,
)
from app.core.jobs import procrastinate_app
from app.core.settings import get_settings
from app.domains.events.constants import EMBED_MAX_ATTEMPTS, REZONE_MAX_ATTEMPTS
from app.domains.events.interactors.dtos import (
    EmbedEventInputDTO,
    QueueMissingEventEmbeddingsInputDTO,
)

logger = structlog.get_logger(__name__)


@lru_cache
def _session_factory() -> async_sessionmaker[AsyncSession]:
    return create_session_factory(create_engine(get_settings()))


@procrastinate_app.periodic(cron="*/15 * * * *")  # every 15 minutes (AD-4, Q3)
@procrastinate_app.task(name="events.roll_yearly")
async def roll_yearly(timestamp: int) -> None:
    """Move ended yearly events on a year and re-arm their alerts; arm any
    event whose alerts were left pending (4.2 Q1). Safe to run twice."""
    session_factory = _session_factory()
    async with session_factory() as session:
        counts = await build_roll_yearly_interactor(
            session=session, session_factory=session_factory
        ).roll_yearly()
    logger.info(
        "events.roll_yearly", rolled_count=counts.rolled, repaired_count=counts.repaired
    )


@procrastinate_app.periodic(cron="47 2 * * *")  # nightly, at 02:47 UTC (NFR-4)
@procrastinate_app.task(name="events.reconcile_alerts")
async def reconcile_alerts(timestamp: int) -> None:
    """Count events whose alerts are out of step. Repairs nothing."""
    async with _session_factory()() as session:
        await build_reconcile_event_alerts_interactor(session).reconcile_alerts()


@procrastinate_app.task(
    name="events.timezone_changed",
    retry=RetryStrategy(max_attempts=REZONE_MAX_ATTEMPTS, exponential_wait=2),
)
async def timezone_changed(user_id: str) -> None:
    """Move one user's events and their alerts to their new zone (FR-12,
    FR-13). Deferred by identity by name; safe to repeat."""
    session_factory = _session_factory()
    async with session_factory() as session:
        moved_count = await build_rezone_events_interactor(
            session=session, session_factory=session_factory
        ).rezone_events(user_id=UUID(user_id))
    logger.info("events.rezoned", user_id=user_id, moved_count=moved_count)


@procrastinate_app.task(
    name="events.embed_event",
    retry=RetryStrategy(max_attempts=EMBED_MAX_ATTEMPTS, exponential_wait=2),
)
async def embed_event(user_id: str, event_id: str) -> None:
    """Give one event its meaning vector (FR-30, 005 AD-7). Safe to run twice.
    Runs inside a ``user_transaction`` for the event's own user."""
    session_factory = _session_factory()
    async with session_factory() as session:
        embedded = await build_embed_event_interactor(
            session=session, session_factory=session_factory
        ).embed_event(
            dto=EmbedEventInputDTO(user_id=UUID(user_id), event_id=UUID(event_id))
        )
    logger.info("events.embed_event", event_id=event_id, embedded=embedded)


@procrastinate_app.periodic(cron="*/10 * * * *")  # every 10 minutes, as 004 P-6
@procrastinate_app.task(name="events.backfill_embeddings")
async def backfill_embeddings(timestamp: int, full: bool = False) -> None:
    """Queue a vector for events with none. ``full`` is deferred once, by
    hand, at deploy (4.2 T-2.16); the periodic run covers recent ones only."""
    async with _session_factory()() as session:
        queued_count = await build_queue_missing_event_embeddings_interactor(
            session
        ).queue_missing_event_embeddings(
            dto=QueueMissingEventEmbeddingsInputDTO(full=full)
        )
    logger.info("events.backfill_embeddings", queued_count=queued_count, full=full)
