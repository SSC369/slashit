"""Repository contracts. Protocols, so a fake needs no inheritance."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID

from app.domains.memories.interfaces.dtos import (
    MemoryCategory,
    MemoryDTO,
    MemoryOriginValue,
    MissingEmbeddingDTO,
)

# FR-16: a category, the uncategorised memories, or every memory (None).
CategoryFilter = MemoryCategory | Literal["uncategorised"] | None


@dataclass(frozen=True)
class MemoryWrite:
    """What a save stores."""

    text: str
    category: MemoryCategory | None
    # None for a save resolved from a conflict: the reembed job fills it, so
    # an answer never waits on the model (sub-plan 4.3, Q1).
    embedding: tuple[float, ...] | None
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

    async def find_nearest(
        self, *, user_id: UUID, embedding: tuple[float, ...], limit: int
    ) -> list[MemoryDTO]:
        """This user's live memories that have a vector, nearest first by
        cosine distance (AD-5). A forgotten memory has no vector, so it is
        never returned."""
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

    async def delete_memories(self, *, user_id: UUID, memory_ids: list[UUID]) -> int:
        """Delete the caller's live memories among these ids (AD-2, amended
        2026-09-27). Returns how many rows it deleted."""
        ...

    async def set_embedding(
        self, *, user_id: UUID, memory_id: UUID, embedding: tuple[float, ...]
    ) -> None:
        """Store a vector on a live memory. Does nothing on a forgotten one."""
        ...

    async def select_missing_embeddings(
        self, *, updated_since: datetime, limit: int
    ) -> list[MissingEmbeddingDTO]:
        """Live memories of every user with no vector, touched since the given
        time. For the backfill job only: reads across users."""
        ...
