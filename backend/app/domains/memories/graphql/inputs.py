"""Memories' GraphQL inputs."""

import strawberry

from app.domains.memories.interfaces.dtos import MemoryCategory


@strawberry.input
class MemoriesFilterInput:
    """FR-16. `uncategorised` wins over `category` when both are set."""

    category: MemoryCategory | None = None
    uncategorised: bool = False
    search: str | None = None


@strawberry.input
class UpdateMemoryInput:
    text: str
    category: MemoryCategory | None
