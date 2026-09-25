"""Input DTOs, one per use case."""

from dataclasses import dataclass
from uuid import UUID

from app.domains.memories.interfaces.dtos import MemoryCategory
from app.domains.memories.interfaces.repositories import CategoryFilter


@dataclass(frozen=True)
class ListMemoriesInputDTO:
    user_id: UUID
    category: CategoryFilter
    search: str | None


@dataclass(frozen=True)
class GetMemoryInputDTO:
    user_id: UUID
    memory_id: UUID


@dataclass(frozen=True)
class UpdateMemoryInputDTO:
    """The edit form, whole (FR-18)."""

    user_id: UUID
    memory_id: UUID
    text: str
    category: MemoryCategory | None


@dataclass(frozen=True)
class ReembedMemoryInputDTO:
    user_id: UUID
    memory_id: UUID
