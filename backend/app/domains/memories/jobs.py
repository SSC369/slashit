"""Memories' Procrastinate task. Thin: resolve collaborators, call one
interactor. See backend/.claude/rules/repo-rules.md section 14.

Runs inside a ``user_transaction`` for the memory's own user, so Row Level
Security binds the job as it binds a request.
"""

from functools import lru_cache
from uuid import UUID

import structlog
from procrastinate import RetryStrategy
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.db import create_engine, create_session_factory
from app.core.deps import build_reembed_memory_interactor
from app.core.jobs import procrastinate_app
from app.core.settings import get_settings
from app.domains.memories.constants import REEMBED_MAX_ATTEMPTS
from app.domains.memories.interactors.dtos import ReembedMemoryInputDTO

logger = structlog.get_logger(__name__)


@lru_cache
def _session_factory() -> async_sessionmaker[AsyncSession]:
    return create_session_factory(create_engine(get_settings()))


@procrastinate_app.task(
    name="memories.reembed",
    retry=RetryStrategy(max_attempts=REEMBED_MAX_ATTEMPTS, exponential_wait=2),
)
async def reembed(user_id: str, memory_id: str) -> None:
    """Refresh one memory's vector after an edit. Safe to run twice."""
    session_factory = _session_factory()
    async with session_factory() as session:
        interactor = build_reembed_memory_interactor(
            session=session, session_factory=session_factory
        )
        refreshed = await interactor.reembed_memory(
            dto=ReembedMemoryInputDTO(user_id=UUID(user_id), memory_id=UUID(memory_id))
        )
    logger.info("memories.reembed", memory_id=memory_id, refreshed=refreshed)
