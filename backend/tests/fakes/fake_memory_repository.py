"""An in-memory MemoryRepository, and fakes for memories' own ports."""

import uuid
from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID

from app.domains.memories.interfaces.dtos import (
    CandidateMemory,
    CategoryJudgement,
    MemoryCategory,
    MemoryDTO,
    ModelRefused,
)
from app.domains.memories.interfaces.ports import MemoryEventType
from app.domains.memories.interfaces.repositories import CategoryFilter, MemoryWrite
from app.domains.memories.services.keyword_query import build_lookup_terms


class FakeMemoryRepository:
    def __init__(self) -> None:
        self.rows: dict[UUID, MemoryDTO] = {}
        self.embeddings: dict[UUID, tuple[float, ...] | None] = {}

    async def create_memory(self, *, user_id: UUID, write: MemoryWrite) -> MemoryDTO:
        now = datetime.now(UTC)
        memory = MemoryDTO(
            id=uuid.uuid4(),
            user_id=user_id,
            text=write.text,
            category=write.category,
            origin=write.origin,
            original_input=write.original_input,
            created_at=now,
            updated_at=now,
        )
        self.rows[memory.id] = memory
        self.embeddings[memory.id] = write.embedding
        return memory

    async def get_by_id(self, *, user_id: UUID, memory_id: UUID) -> MemoryDTO | None:
        memory = self.rows.get(memory_id)
        return memory if memory and memory.user_id == user_id else None

    async def list_for_user(
        self, *, user_id: UUID, category: CategoryFilter, search: str | None
    ) -> list[MemoryDTO]:
        owned = [row for row in self.rows.values() if row.user_id == user_id]
        if category == "uncategorised":
            owned = [row for row in owned if row.category is None]
        elif category is not None:
            owned = [row for row in owned if row.category == category]
        if search:
            owned = [row for row in owned if search.lower() in row.text.lower()]
        return sorted(owned, key=lambda row: row.created_at, reverse=True)

    async def find_by_terms(
        self, *, user_id: UUID, terms: list[str], limit: int
    ) -> list[MemoryDTO]:
        def matches(memory: MemoryDTO) -> int:
            words = set(build_lookup_terms(text=memory.text))
            return sum(1 for term in terms if term in words)

        owned = [row for row in self.rows.values() if row.user_id == user_id]
        found = [row for row in owned if matches(row) > 0]
        return sorted(found, key=matches, reverse=True)[:limit]

    async def update_text_and_category(
        self,
        *,
        user_id: UUID,
        memory_id: UUID,
        text: str,
        category: MemoryCategory | None,
    ) -> MemoryDTO | None:
        memory = await self.get_by_id(user_id=user_id, memory_id=memory_id)
        if memory is None:
            return None
        updated = replace(
            memory,
            text=text,
            category=category,
            origin="edit",
            updated_at=datetime.now(UTC),
        )
        self.rows[memory_id] = updated
        self.embeddings[memory_id] = None
        return updated

    async def set_embedding(
        self, *, user_id: UUID, memory_id: UUID, embedding: tuple[float, ...]
    ) -> None:
        if await self.get_by_id(user_id=user_id, memory_id=memory_id):
            self.embeddings[memory_id] = embedding


class FakeMemoryModel:
    """Both model ports at once. Set a refusal to make either call fail."""

    def __init__(
        self,
        *,
        category: MemoryCategory | None = MemoryCategory.LIFE,
        embed_refusal: object | None = None,
        judge_refusal: object | None = None,
    ) -> None:
        self.category = category
        self.embed_refusal = embed_refusal
        self.judge_refusal = judge_refusal
        self.embedded_texts: list[str] = []
        self.judged_texts: list[str] = []

    async def embed_fact(
        self, *, user_id: UUID, text: str
    ) -> tuple[float, ...] | ModelRefused:
        self.embedded_texts.append(text)
        if self.embed_refusal is not None:
            return ModelRefused(gateway_result=self.embed_refusal)
        return (0.1, 0.2, 0.3)

    async def judge_fact(
        self, *, user_id: UUID, text: str, candidates: list[CandidateMemory]
    ) -> CategoryJudgement | ModelRefused:
        self.judged_texts.append(text)
        if self.judge_refusal is not None:
            return ModelRefused(gateway_result=self.judge_refusal)
        return CategoryJudgement(category=self.category, conflicting_ids=())


class FakeMemoryAnalytics:
    def __init__(self) -> None:
        self.events: list[MemoryEventType] = []

    async def record_memory_event(
        self, *, user_id: UUID, event_type: MemoryEventType
    ) -> None:
        self.events.append(event_type)


class FakeReembedQueue:
    def __init__(self) -> None:
        self.queued: list[UUID] = []

    async def enqueue_reembed(self, *, user_id: UUID, memory_id: UUID) -> None:
        self.queued.append(memory_id)
