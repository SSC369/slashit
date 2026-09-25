"""Repository contracts. Protocols, so a fake needs no inheritance."""

from dataclasses import dataclass
from typing import Literal, Protocol
from uuid import UUID

from app.domains.memories.interfaces.dtos import (
    MemoryCategory,
    MemoryDTO,
    MemoryOriginValue,
)

# FR-16: a category, the uncategorised memories, or every memory (None).
CategoryFilter = MemoryCategory | Literal["uncategorised"] | None


@dataclass(frozen=True)
class MemoryWrite:
    """What a save stores."""

    text: str
    category: MemoryCategory | None
    embedding: tuple[float, ...]
    origin: MemoryOriginValue
    original_input: str | None


class MemoryRepository(Protocol):
    async def create_memory(self, *, user_id: UUID, write: MemoryWrite) -> MemoryDTO:
        """Insert one memory, committed."""
        ...

    async def get_by_id(self, *, user_id: UUID, memory_id: UUID) -> MemoryDTO | None:
        """One live memory this user owns, or None. Forgotten reads as None."""
        ...

    async def list_for_user(
        self, *, user_id: UUID, category: CategoryFilter, search: str | None
    ) -> list[MemoryDTO]:
        """Live memories, newest first, filtered by category and a substring."""
        ...

    async def find_by_terms(
        self, *, user_id: UUID, terms: list[str], limit: int
    ) -> list[MemoryDTO]:
        """Live memories matching any term, most matches first (FR-20)."""
        ...

    async def update_text_and_category(
        self,
        *,
        user_id: UUID,
        memory_id: UUID,
        text: str,
        category: MemoryCategory | None,
    ) -> MemoryDTO | None:
        """Edit one live memory, clearing its vector until the reembed job
        refills it. None when it is not this user's live memory."""
        ...

    async def filter_live_ids(
        self, *, user_id: UUID, memory_ids: list[UUID]
    ) -> list[UUID]:
        """The subset of ids that are this user's live memories."""
        ...

    async def list_live_ids(self, *, user_id: UUID) -> list[UUID]:
        """Every live memory id this user holds, for forget-all."""
        ...

    async def count_by_terms(self, *, user_id: UUID, terms: list[str]) -> int:
        """How many live memories match any term, for "{n} more match"."""
        ...

    async def tombstone_memories(self, *, user_id: UUID, memory_ids: list[UUID]) -> int:
        """Stamp ``deleted_at`` and set every readable column to NULL, in one
        UPDATE (AD-2). Returns how many live rows it changed."""
        ...

    async def set_embedding(
        self, *, user_id: UUID, memory_id: UUID, embedding: tuple[float, ...]
    ) -> None:
        """Store a vector on a live memory. Does nothing on a forgotten one."""
        ...
