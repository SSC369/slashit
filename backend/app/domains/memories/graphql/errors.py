"""Memories' failure outcomes, as union members and exceptions together.

Both faces of an error live in this one file, per repo-rules.md sections 7.1
and 8. ``MemoryTooLong`` is the one exception: its type lives in
``interfaces/dtos.py`` because capture returns it too.
"""

import strawberry

from app.core.errors import DomainError
from app.domains.memories.constants import MAX_FACT_LENGTH
from app.domains.memories.interfaces.dtos import MemoryTooLong


@strawberry.type
class MemoryNotFound:
    message: str


class MemoryNotFoundError(DomainError):
    gql_type = MemoryNotFound

    def __init__(self) -> None:
        super().__init__("This memory doesn't exist or was forgotten.")


@strawberry.type
class InvalidMemory:
    message: str


class InvalidMemoryError(DomainError):
    gql_type = InvalidMemory

    def __init__(self, *, message: str) -> None:
        super().__init__(message)


class MemoryTooLongError(DomainError):
    gql_type = MemoryTooLong

    def __init__(self, *, length: int) -> None:
        self.length = length
        self.limit = MAX_FACT_LENGTH
        super().__init__(
            f"That is {length} characters. A memory can be up to {MAX_FACT_LENGTH}."
        )
