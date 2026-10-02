"""Implements search's AnswerPort against the gateway (FR-16, build plan §5)."""

from collections.abc import Sequence
from datetime import date
from typing import Any, cast
from uuid import UUID

import structlog

from app.domains.gateway.public import (
    ExtractInteractor,
    Extraction,
    ExtractionRequest,
    UserLimitReached,
)
from app.domains.search.constants import ANSWER_INSTRUCTION, ANSWER_SCHEMA
from app.domains.search.interfaces.dtos import (
    AnswerDraftDTO,
    AnswerRecordDTO,
    AnswerRefusedDTO,
)

logger = structlog.get_logger(__name__)


class GatewayAnswerAdapter:
    def __init__(self, *, extract_interactor: ExtractInteractor) -> None:
        self.extract_interactor = extract_interactor

    async def write_answer(
        self,
        *,
        user_id: UUID,
        question: str,
        today: date,
        records: Sequence[AnswerRecordDTO],
    ) -> AnswerDraftDTO | AnswerRefusedDTO:
        """A refusal on any gateway failure: the unavailable line, not an error
        (FR-19). Counts against the per-user cap, as every generation does."""
        extraction_result = await self.extract_interactor.extract(
            user_id=user_id,
            request=ExtractionRequest(
                prompt=build_answer_prompt(
                    question=question, today=today, records=records
                ),
                schema=ANSWER_SCHEMA,
                instruction=ANSWER_INSTRUCTION,
            ),
        )
        if not isinstance(extraction_result, Extraction):
            logger.warning(
                "search.answer_refused", result=type(extraction_result).__name__
            )
            return AnswerRefusedDTO(
                limit_reached=isinstance(extraction_result, UserLimitReached)
            )
        return _read_draft(fields=cast(dict[str, Any], extraction_result.data))


def build_answer_prompt(
    *, question: str, today: date, records: Sequence[AnswerRecordDTO]
) -> str:
    """The question, today's date, and the numbered records. No id reaches
    the model: it cites by number, and search maps numbers back (AD-5)."""
    lines = [
        f"Today: {today.strftime('%A %d %B %Y')}",
        f"Question: {question}",
        "Records:",
    ]
    lines.extend(
        f"[{record.number}] {record.text} ({record.detail})" for record in records
    )
    return "\n".join(lines)


def _read_draft(*, fields: dict[str, Any]) -> AnswerDraftDTO:
    """Tolerant of shape: anything not a sentence with integer sources is
    left out here, and AD-5's check then decides what may be shown."""
    raw_sentences = fields.get("sentences")
    sentences: list[tuple[str, list[int]]] = []
    if isinstance(raw_sentences, list):
        for raw_sentence in raw_sentences:
            if not isinstance(raw_sentence, dict):
                continue
            text = raw_sentence.get("text")
            raw_sources = raw_sentence.get("sources")
            if not isinstance(text, str) or not isinstance(raw_sources, list):
                continue
            sources = [
                source
                for source in raw_sources
                if isinstance(source, int) and not isinstance(source, bool)
            ]
            sentences.append((text, sources))
    return AnswerDraftDTO(
        sentences=sentences, supported=fields.get("supported") is True
    )
