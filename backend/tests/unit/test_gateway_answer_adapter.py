"""Epic 005, sub-plan 4.2, C-2.8: what the model is shown, and how its reply
is read (FR-16, NFR-1, build plan §5)."""

import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any

from app.domains.gateway.public import (
    Extraction,
    ExtractionRequest,
    ProviderUnavailable,
    UserLimitReached,
)
from app.domains.search.adapters.gateway_answer_adapter import (
    GatewayAnswerAdapter,
    build_answer_prompt,
)
from app.domains.search.interfaces.dtos import (
    AnswerRecordDTO,
    AnswerRefusedDTO,
    RecordType,
)

UUID_PATTERN = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-")


def _records(count: int) -> list[AnswerRecordDTO]:
    return [
        AnswerRecordDTO(
            number=number,
            record_type=RecordType.TASK,
            text=f"Task {number}",
            detail="task, no due date, pending",
        )
        for number in range(1, count + 1)
    ]


def test_the_prompt_numbers_the_records_and_holds_no_id() -> None:
    prompt = build_answer_prompt(
        question="What is due?", today=date(2026, 9, 30), records=_records(10)
    )

    assert "Question: What is due?" in prompt
    assert "Today: Wednesday 30 September 2026" in prompt
    assert "[1] Task 1 (task, no due date, pending)" in prompt
    assert "[10] Task 10" in prompt
    assert not UUID_PATTERN.search(prompt)


@dataclass
class _Extractor:
    data: dict[str, Any] | None
    refusal: object = field(default_factory=lambda: ProviderUnavailable(message="down"))
    requests: list[ExtractionRequest] = field(default_factory=list)

    async def extract(
        self, *, user_id: uuid.UUID, request: ExtractionRequest
    ) -> object:
        self.requests.append(request)
        if self.data is None:
            return self.refusal
        return Extraction(data=self.data, model="fake", input_tokens=1, output_tokens=1)


async def test_a_reply_is_read_tolerantly() -> None:
    extractor = _Extractor(
        data={
            "sentences": [
                {"text": "Kept.", "sources": [1, "2", True, 3]},
                {"text": 5, "sources": [1]},
                "not a sentence",
                {"text": "No sources key."},
            ],
            "supported": True,
        }
    )
    adapter = GatewayAnswerAdapter(extract_interactor=extractor)  # type: ignore[arg-type]

    draft = await adapter.write_answer(
        user_id=uuid.uuid4(), question="q", today=date(2026, 9, 30), records=_records(3)
    )

    assert not isinstance(draft, AnswerRefusedDTO)
    assert draft.sentences == [("Kept.", [1, 3])]
    assert draft.supported is True


async def test_a_gateway_failure_is_a_refusal_not_a_limit() -> None:
    """FR-19: the caller shows the unavailable line."""
    adapter = GatewayAnswerAdapter(extract_interactor=_Extractor(data=None))  # type: ignore[arg-type]

    draft = await adapter.write_answer(
        user_id=uuid.uuid4(), question="q", today=date(2026, 9, 30), records=_records(1)
    )

    assert draft == AnswerRefusedDTO(limit_reached=False)


async def test_the_daily_limit_is_a_refusal_that_says_so() -> None:
    """Q7: the per-user cap is told apart from an outage."""
    extractor = _Extractor(
        data=None,
        refusal=UserLimitReached(
            message="limit", limit=20, resets_at=datetime(2026, 10, 3, tzinfo=UTC)
        ),
    )
    adapter = GatewayAnswerAdapter(extract_interactor=extractor)  # type: ignore[arg-type]

    draft = await adapter.write_answer(
        user_id=uuid.uuid4(), question="q", today=date(2026, 9, 30), records=_records(1)
    )

    assert draft == AnswerRefusedDTO(limit_reached=True)
