"""004 P-6: the backfill sweep's query against a real database."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domains.memories.interfaces.repositories import MemoryWrite
from app.domains.memories.repositories.memory_repository import SqlMemoryRepository


async def test_the_sweep_finds_a_live_memory_with_no_vector(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    user_id, _ = two_users
    async with session_factory() as session:
        repository = SqlMemoryRepository(session)
        memory = await repository.create_memory(
            user_id=user_id,
            write=MemoryWrite(
                text="Gym is Cult Fit",
                category=None,
                embedding=None,
                origin="command",
                original_input=None,
            ),
        )
        found = await repository.select_missing_embeddings(
            updated_since=datetime.now(UTC) - timedelta(hours=1), limit=1000
        )
        await repository.set_embedding(
            user_id=user_id, memory_id=memory.id, embedding=(0.1,) * 768
        )
        after = await repository.select_missing_embeddings(
            updated_since=datetime.now(UTC) - timedelta(hours=1), limit=1000
        )

    assert memory.id in [row.memory_id for row in found]
    assert memory.id not in [row.memory_id for row in after]
