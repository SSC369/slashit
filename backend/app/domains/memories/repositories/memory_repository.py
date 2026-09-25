"""The only SQL in the memories domain. Returns DTOs, never models."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import user_transaction
from app.domains.memories.interfaces.dtos import (
    MemoryCategory,
    MemoryDTO,
    MemoryOriginValue,
)
from app.domains.memories.interfaces.repositories import CategoryFilter, MemoryWrite
from app.domains.memories.models import Memory


class SqlMemoryRepository:
    """Reads and writes ``memories`` against the request's own session."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_memory(
        self, *, user_id: uuid.UUID, write: MemoryWrite
    ) -> MemoryDTO:
        now = datetime.now(UTC)
        memory = Memory(
            id=uuid.uuid4(),
            user_id=user_id,
            text=write.text,
            category=write.category.value if write.category else None,
            embedding=list(write.embedding),
            origin=write.origin,
            original_input=write.original_input,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )
        async with user_transaction(self.session, user_id) as scoped:
            scoped.add(memory)
        return _memory_to_dto(memory=memory)

    async def get_by_id(
        self, *, user_id: uuid.UUID, memory_id: uuid.UUID
    ) -> MemoryDTO | None:
        async with user_transaction(self.session, user_id) as scoped:
            memory = await scoped.scalar(
                _live_for(user_id=user_id).where(Memory.id == memory_id)
            )
            return _memory_to_dto(memory=memory) if memory else None

    async def list_for_user(
        self, *, user_id: uuid.UUID, category: CategoryFilter, search: str | None
    ) -> list[MemoryDTO]:
        query = _live_for(user_id=user_id)
        if category == "uncategorised":
            query = query.where(Memory.category.is_(None))
        elif category is not None:
            query = query.where(Memory.category == category.value)
        if search:
            query = query.where(Memory.text.ilike(f"%{_escape_like(text=search)}%"))
        query = query.order_by(Memory.created_at.desc(), Memory.id.desc())
        async with user_transaction(self.session, user_id) as scoped:
            memories = (await scoped.scalars(query)).all()
            return [_memory_to_dto(memory=memory) for memory in memories]

    async def find_by_terms(
        self, *, user_id: uuid.UUID, terms: list[str], limit: int
    ) -> list[MemoryDTO]:
        if not terms:
            return []
        # Terms are letters and digits only (keyword_query), so joining them
        # into to_tsquery's syntax cannot inject an operator.
        text_query = func.to_tsquery("english", " | ".join(terms))
        rank = func.ts_rank(Memory.search_vector, text_query)
        query = (
            _live_for(user_id=user_id)
            .where(Memory.search_vector.op("@@")(text_query))
            .order_by(rank.desc(), Memory.created_at.desc())
            .limit(limit)
        )
        async with user_transaction(self.session, user_id) as scoped:
            memories = (await scoped.scalars(query)).all()
            return [_memory_to_dto(memory=memory) for memory in memories]

    async def update_text_and_category(
        self,
        *,
        user_id: uuid.UUID,
        memory_id: uuid.UUID,
        text: str,
        category: MemoryCategory | None,
    ) -> MemoryDTO | None:
        async with user_transaction(self.session, user_id) as scoped:
            memory = await scoped.scalar(
                _live_for(user_id=user_id)
                .where(Memory.id == memory_id)
                .with_for_update()
            )
            if memory is None:
                return None
            memory.text = text
            memory.category = category.value if category else None
            memory.origin = "edit"
            # The old vector describes the old text. NULL until reembed runs,
            # so a stale vector is never a conflict candidate (slice 2).
            memory.embedding = None
            memory.updated_at = datetime.now(UTC)
            await scoped.flush()
            return _memory_to_dto(memory=memory)

    async def filter_live_ids(
        self, *, user_id: uuid.UUID, memory_ids: list[uuid.UUID]
    ) -> list[uuid.UUID]:
        if not memory_ids:
            return []
        async with user_transaction(self.session, user_id) as scoped:
            live_ids = await scoped.scalars(
                select(Memory.id).where(
                    Memory.user_id == user_id,
                    Memory.deleted_at.is_(None),
                    Memory.id.in_(memory_ids),
                )
            )
            return list(live_ids)

    async def list_live_ids(self, *, user_id: uuid.UUID) -> list[uuid.UUID]:
        async with user_transaction(self.session, user_id) as scoped:
            live_ids = await scoped.scalars(
                select(Memory.id).where(
                    Memory.user_id == user_id, Memory.deleted_at.is_(None)
                )
            )
            return list(live_ids)

    async def count_by_terms(self, *, user_id: uuid.UUID, terms: list[str]) -> int:
        if not terms:
            return 0
        text_query = func.to_tsquery("english", " | ".join(terms))
        async with user_transaction(self.session, user_id) as scoped:
            matched_count = await scoped.scalar(
                select(func.count())
                .select_from(Memory)
                .where(
                    Memory.user_id == user_id,
                    Memory.deleted_at.is_(None),
                    Memory.search_vector.op("@@")(text_query),
                )
            )
        return int(matched_count or 0)

    async def tombstone_memories(
        self, *, user_id: uuid.UUID, memory_ids: list[uuid.UUID]
    ) -> int:
        if not memory_ids:
            return 0
        now = datetime.now(UTC)
        async with user_transaction(self.session, user_id) as scoped:
            forgotten_ids = await scoped.scalars(
                update(Memory)
                .where(
                    Memory.user_id == user_id,
                    Memory.deleted_at.is_(None),
                    Memory.id.in_(memory_ids),
                )
                .values(
                    deleted_at=now,
                    updated_at=now,
                    text=None,
                    original_input=None,
                    category=None,
                    embedding=None,
                )
                .returning(Memory.id)
            )
            return len(list(forgotten_ids))

    async def set_embedding(
        self,
        *,
        user_id: uuid.UUID,
        memory_id: uuid.UUID,
        embedding: tuple[float, ...],
    ) -> None:
        async with user_transaction(self.session, user_id) as scoped:
            await scoped.execute(
                update(Memory)
                .where(
                    Memory.id == memory_id,
                    Memory.user_id == user_id,
                    Memory.deleted_at.is_(None),
                )
                .values(embedding=list(embedding))
            )


def _live_for(*, user_id: uuid.UUID) -> Select[tuple[Memory]]:
    """Live memories of one user. RLS is the second lock; this is the first."""
    return select(Memory).where(Memory.user_id == user_id, Memory.deleted_at.is_(None))


def _escape_like(*, text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _memory_to_dto(*, memory: Memory) -> MemoryDTO:
    origin: MemoryOriginValue = "edit" if memory.origin == "edit" else "command"
    return MemoryDTO(
        id=memory.id,
        user_id=memory.user_id,
        text=memory.text or "",
        category=MemoryCategory(memory.category) if memory.category else None,
        origin=origin,
        original_input=memory.original_input,
        created_at=memory.created_at,
        updated_at=memory.updated_at,
    )
