"""Epic 005, sub-plan 4.3, C-3.6: related records (FR-25, FR-26, AD-6)."""

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domains.records.public import TaskDTO
from app.domains.search.constants import RELATED_LIMIT, RELATED_MAX_DISTANCE
from app.domains.search.interfaces.dtos import (
    CandidatePageDTO,
    RecordType,
    SearchCandidate,
)
from tests.unit.test_search_service import _Embedder, _service

NOW = datetime(2026, 9, 30, tzinfo=UTC)
SOURCE_VECTOR = (0.1,) * 768


def _task(*, title: str) -> TaskDTO:
    return TaskDTO(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        title=title,
        due_at=None,
        status="pending",
        is_overdue=False,
        origin="command",
        original_input=None,
        created_at=NOW,
        updated_at=NOW,
    )


@dataclass
class _VectorPort:
    """Holds records at fixed distances from any query vector."""

    record_type: RecordType
    records: list[tuple[TaskDTO, float]]
    vectors: dict[uuid.UUID, tuple[float, ...]] = field(default_factory=dict)
    calls: list[tuple[tuple[str, ...], float, int]] = field(default_factory=list)

    async def search_candidates(
        self,
        *,
        user_id: uuid.UUID,
        text: str,
        terms: Sequence[str],
        query_embedding: Sequence[float] | None,
        max_distance: float,
        limit: int,
    ) -> CandidatePageDTO:
        self.calls.append((tuple(terms), max_distance, limit))
        within = sorted(
            (pair for pair in self.records if pair[1] < max_distance),
            key=lambda pair: pair[1],
        )
        return CandidatePageDTO(
            candidates=[
                SearchCandidate(
                    record_type=self.record_type,
                    record_id=task.id,
                    item=task,
                    all_terms=False,
                    word_rank=None,
                    distance=distance,
                )
                for task, distance in within[:limit]
            ],
            total=len(within),
        )

    async def embedding_of(
        self, *, user_id: uuid.UUID, record_id: uuid.UUID
    ) -> tuple[float, ...] | None:
        return self.vectors.get(record_id)


async def test_the_nearest_five_across_types_closest_first_without_itself() -> None:
    source = _task(title="Renew passport")
    tasks = _VectorPort(
        record_type=RecordType.TASK,
        records=[
            (source, 0.0),
            (_task(title="Book visa"), 0.12),
            (_task(title="Scan passport"), 0.05),
            (_task(title="Buy milk"), 0.18),
        ],
        vectors={source.id: SOURCE_VECTOR},
    )
    memories = _VectorPort(
        record_type=RecordType.MEMORY,
        records=[
            (_task(title="Passport expires 2030"), 0.02),
            (_task(title="Japan trip"), 0.14),
            (_task(title="Shoe size"), 0.16),
            (_task(title="Too far"), RELATED_MAX_DISTANCE + 0.01),
        ],
    )
    service = _service(ports=[tasks, memories], embedder=_Embedder(vector=None))

    related = await service.related(
        user_id=uuid.uuid4(), record_type=RecordType.TASK, record_id=source.id
    )

    assert [record.item.title for record in related] == [
        "Passport expires 2030",
        "Scan passport",
        "Book visa",
        "Japan trip",
        "Shoe size",
    ]
    assert len(related) == RELATED_LIMIT
    assert [record.record_type for record in related][:2] == [
        RecordType.MEMORY,
        RecordType.TASK,
    ]
    # Words play no part, and each type is asked for one more than is shown.
    assert tasks.calls == [((), RELATED_MAX_DISTANCE, RELATED_LIMIT + 1)]


async def test_a_record_with_nothing_close_has_nothing_related() -> None:
    """FR-26: "Nothing related yet"."""
    source = _task(title="Renew passport")
    tasks = _VectorPort(
        record_type=RecordType.TASK,
        records=[(source, 0.0), (_task(title="Buy milk"), 0.6)],
        vectors={source.id: SOURCE_VECTOR},
    )
    service = _service(ports=[tasks], embedder=_Embedder(vector=None))

    related = await service.related(
        user_id=uuid.uuid4(), record_type=RecordType.TASK, record_id=source.id
    )

    assert related == []


async def test_a_record_with_no_vector_yet_or_not_its_own_has_nothing_related() -> None:
    """AD-6's fallback, and T7: an id the user cannot see has no vector."""
    tasks = _VectorPort(
        record_type=RecordType.TASK, records=[(_task(title="Buy milk"), 0.1)]
    )
    service = _service(ports=[tasks], embedder=_Embedder(vector=None))

    related = await service.related(
        user_id=uuid.uuid4(), record_type=RecordType.TASK, record_id=uuid.uuid4()
    )

    assert related == []
    assert tasks.calls == []
