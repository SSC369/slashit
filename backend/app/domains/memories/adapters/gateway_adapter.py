"""Implements memories' EmbeddingPort and JudgementPort against the gateway."""

from typing import Any, cast
from uuid import UUID

from app.domains.gateway.public import (
    Embedding,
    EmbedInteractor,
    ExtractInteractor,
    Extraction,
    ExtractionRequest,
)
from app.domains.memories.constants import JUDGEMENT_INSTRUCTION, JUDGEMENT_SCHEMA
from app.domains.memories.interfaces.dtos import (
    CandidateMemory,
    CategoryJudgement,
    MemoryCategory,
    ModelRefused,
)


class GatewayMemoryModelAdapter:
    def __init__(
        self,
        *,
        embed_interactor: EmbedInteractor,
        extract_interactor: ExtractInteractor,
    ) -> None:
        self.embed_interactor = embed_interactor
        self.extract_interactor = extract_interactor

    async def embed_fact(
        self, *, user_id: UUID, text: str
    ) -> tuple[float, ...] | ModelRefused:
        embed_result = await self.embed_interactor.embed(user_id=user_id, text=text)
        if isinstance(embed_result, Embedding):
            return embed_result.vector
        return ModelRefused(gateway_result=embed_result)

    async def judge_fact(
        self, *, user_id: UUID, text: str, candidates: list[CandidateMemory]
    ) -> CategoryJudgement | ModelRefused:
        extraction_result = await self.extract_interactor.extract(
            user_id=user_id,
            request=ExtractionRequest(
                prompt=_build_prompt(text=text, candidates=candidates),
                schema=JUDGEMENT_SCHEMA,
                instruction=JUDGEMENT_INSTRUCTION,
            ),
        )
        if not isinstance(extraction_result, Extraction):
            return ModelRefused(gateway_result=extraction_result)
        fields = cast(dict[str, Any], extraction_result.data)
        return CategoryJudgement(
            category=_read_category(raw_category=fields.get("category")),
            conflicting_ids=_read_conflicting_ids(
                raw_ids=fields.get("conflicting_ids"), candidates=candidates
            ),
        )


def _build_prompt(*, text: str, candidates: list[CandidateMemory]) -> str:
    lines = [f"Fact: {text}", "Candidates:"]
    lines.extend(f"- {candidate.id}: {candidate.text}" for candidate in candidates)
    if not candidates:
        lines.append("(none)")
    return "\n".join(lines)


def _read_category(*, raw_category: object) -> MemoryCategory | None:
    """FR-6: anything that is not one of the four saves uncategorised."""
    try:
        return MemoryCategory(str(raw_category))
    except ValueError:
        return None


def _read_conflicting_ids(
    *, raw_ids: object, candidates: list[CandidateMemory]
) -> tuple[UUID, ...]:
    """Only ids that were offered. The model cannot name a memory it was never
    shown, so anything else is dropped rather than trusted (index §4)."""
    if not isinstance(raw_ids, list):
        return ()
    offered = {str(candidate.id): candidate.id for candidate in candidates}
    return tuple(offered[str(raw_id)] for raw_id in raw_ids if str(raw_id) in offered)
