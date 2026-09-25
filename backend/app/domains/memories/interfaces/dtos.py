"""Data crossing the memories domain's boundaries. Frozen, never a model.

The GraphQL shapes ``Memory`` and ``MemoryTooLong`` live here rather than under
``graphql/`` so they may cross into ``capture`` and ``records`` through
``public.py``, the placement ``records`` uses for ``Task`` (repo-rules.md
section 6.2).
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

import strawberry

from app.domains.memories.constants import MAX_FACT_LENGTH

MemoryOriginValue = Literal["command", "edit"]


@strawberry.enum
class MemoryCategory(StrEnum):
    """FR-5: the fixed four, epic Q2."""

    PERSONAL = "personal"
    PEOPLE = "people"
    PROFESSIONAL = "professional"
    LIFE = "life"


@strawberry.enum
class SecretKind(StrEnum):
    """FR-8, AD-8: what made a fact look like a secret. Names why, never the
    matched text."""

    CARD = "card"
    ID_NUMBER = "id_number"
    TAX_ID = "tax_id"
    CREDENTIAL = "credential"


@dataclass(frozen=True)
class MemoryDTO:
    """One live memory, as every layer above the repository sees it."""

    id: UUID
    user_id: UUID
    text: str
    category: MemoryCategory | None
    origin: MemoryOriginValue
    original_input: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class MemorySavedDTO:
    """FR-7: the saved memory, and FR-8's caution when there is one."""

    memory: MemoryDTO
    secret_caution: SecretKind | None


@dataclass(frozen=True)
class MemoryListDTO:
    """FR-19 and FR-20: `/memories`, or `/memories <text>` with its text."""

    memories: list[MemoryDTO]
    search_text: str | None


@dataclass(frozen=True)
class MemoryTooLongDTO:
    """FR-4: nothing was saved; the client keeps the text."""

    length: int
    limit: int = MAX_FACT_LENGTH


@dataclass(frozen=True)
class ModelRefused:
    """A model call failed, so nothing was saved (FR-9).

    ``gateway_result`` is the gateway's own failure member, carried opaque so
    this domain need not know the gateway's types. Capture's adapter, which
    does know them, passes it on unchanged, so the client shows the same
    refusal it shows for a task.
    """

    gateway_result: object


@dataclass(frozen=True)
class ForgetCandidatesDTO:
    """What `/forget <which>` offers (FR-24 to FR-27). Nothing is forgotten
    until the user confirms, so this carries no side effect."""

    search_text: str
    candidates: list[MemoryDTO]
    total_matches: int
    forget_all: bool
    all_count: int


@dataclass(frozen=True)
class MemoriesForgottenDTO:
    """How many memories a forget removed. Zero means none were the caller's
    live memories, which the resolvers answer as not found."""

    count: int


@dataclass(frozen=True)
class MemoryCountChangedDTO:
    """FR-27: the count confirmed is no longer the count held, so nothing was
    forgotten and the user is asked again."""

    count: int


@dataclass(frozen=True)
class CategoryJudgement:
    """What the model said about one fact: its category, and which of the
    candidates it contradicts. Slice 1 sends no candidates."""

    category: MemoryCategory | None
    conflicting_ids: tuple[UUID, ...]


@dataclass(frozen=True)
class CandidateMemory:
    """One existing memory offered to the model for the conflict check."""

    id: UUID
    text: str


@strawberry.type
class Memory:
    """FR-17: every stored field the detail shows."""

    id: strawberry.ID
    text: str
    category: MemoryCategory | None
    origin: str
    original_input: str | None
    created_at: datetime
    updated_at: datetime


@strawberry.type
class MemoryTooLong:
    """FR-4 and FR-18: "That is 612 characters. A memory can be up to 500." """

    message: str
    length: int
    limit: int


@strawberry.type
class MemoriesForgotten:
    """FR-22: the memories are gone. Shared by Records and capture."""

    count: int


@strawberry.type
class MemoryCountChanged:
    """FR-27: "You now have {count} memories", and the confirm asks again."""

    message: str
    count: int


def memory_dto_to_type(*, memory: MemoryDTO) -> Memory:
    return Memory(
        id=strawberry.ID(str(memory.id)),
        text=memory.text,
        category=memory.category,
        origin=memory.origin,
        original_input=memory.original_input,
        created_at=memory.created_at,
        updated_at=memory.updated_at,
    )


def memory_too_long_to_type(*, too_long: MemoryTooLongDTO) -> MemoryTooLong:
    return MemoryTooLong(
        message=(
            f"That is {too_long.length} characters. "
            f"A memory can be up to {too_long.limit}."
        ),
        length=too_long.length,
        limit=too_long.limit,
    )
