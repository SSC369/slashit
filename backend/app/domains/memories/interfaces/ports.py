"""What memories needs from other domains, in its own words.

Per repo-rules.md section 6, the port belongs to the consumer. None of these
names the gateway or analytics; each names the one thing memories needs.
"""

from typing import Literal, Protocol
from uuid import UUID

from app.domains.memories.interfaces.dtos import (
    CandidateMemory,
    CategoryJudgement,
    ModelRefused,
)

MemoryEventType = Literal[
    "memory_saved",
    "memory_lookup",
    "memory_conflict_answered",
    "memory_forgotten",
    "memory_category_edited",
    "memory_secret_caution",
]


class EmbeddingPort(Protocol):
    """A meaning vector for one fact (AD-4)."""

    async def embed_fact(
        self, *, user_id: UUID, text: str
    ) -> tuple[float, ...] | ModelRefused: ...


class JudgementPort(Protocol):
    """The fact's category and the candidates it contradicts, in one call."""

    async def judge_fact(
        self, *, user_id: UUID, text: str, candidates: list[CandidateMemory]
    ) -> CategoryJudgement | ModelRefused: ...


class MemoryAnalyticsPort(Protocol):
    """PRD section 8's events. Ids and kinds only, never text (AD-9)."""

    async def record_memory_event(
        self, *, user_id: UUID, event_type: MemoryEventType
    ) -> None: ...


class TurnScrubPort(Protocol):
    """FR-23: erase the words of every capture turn that saved these memories.

    Owned by memories, implemented by capture's ``CaptureTurnScrubber``, which
    satisfies it structurally and imports nothing from memories, so the domain
    graph stays acyclic (build plan §2). Wired in ``core/deps.py``.
    """

    async def scrub_turns_for_memories(
        self, *, user_id: UUID, memory_ids: list[UUID]
    ) -> int: ...


class ReembedQueue(Protocol):
    """Queues the vector's refresh after an edit, so an edit never waits on,
    or fails with, the model (build plan §7)."""

    async def enqueue_reembed(self, *, user_id: UUID, memory_id: UUID) -> None: ...
