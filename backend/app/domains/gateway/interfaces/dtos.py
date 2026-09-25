"""Data crossing the gateway's boundaries. Frozen, and never a model instance."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

OperationValue = Literal["generate", "embed"]


@dataclass(frozen=True)
class ExtractionRequest:
    """What a caller asks for.

    ``schema`` is a JSON Schema describing the shape the caller wants back. The
    caller owns it; the gateway only passes it to the provider and validates
    against it.
    """

    prompt: str
    schema: dict[str, Any]
    instruction: str | None = None


@dataclass(frozen=True)
class ProviderResult:
    """What a provider returns on success.

    Token counts are the provider's own, not an estimate, because FR-11 records
    what was actually consumed.
    """

    data: dict[str, Any]
    input_tokens: int
    output_tokens: int
    model: str


@dataclass(frozen=True)
class ProviderEmbedding:
    """What a provider returns for one embedding. The provider reports no
    token count for an embedding, so none is carried."""

    vector: tuple[float, ...]
    model: str


@dataclass(frozen=True)
class Embedding:
    """Success for a caller of ``EmbedInteractor``. Epic 004."""

    vector: tuple[float, ...]
    model: str


@dataclass(frozen=True)
class AllowanceDTO:
    """A user's remaining headroom."""

    limit: int
    used: int
    resets_at: datetime

    @property
    def remaining(self) -> int:
        return max(self.limit - self.used, 0)

    @property
    def has_capacity(self) -> bool:
        return self.remaining > 0


@dataclass(frozen=True)
class UsageRecord:
    """One row of ai_usage.

    Note what is absent: there is no field for the prompt, the response, or any
    part of the user's text. Requirement FR-12 forbids it, and the way to keep
    that true is to leave nowhere to put it.
    """

    id: UUID
    user_id: UUID
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    outcome: str
    latency_ms: int | None
    # Epic 004. Every call before embeddings existed was a generation.
    operation: OperationValue = "generate"

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens
