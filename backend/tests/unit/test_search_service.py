"""Epic 005, sub-plan 4.1, C-4, C-4b and C-12: the search service's fallback,
its parallel embed, and its coverage of every record type (FR-11, FR-20,
AD-4, AD-11)."""

import asyncio
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domains.records.public import TaskDTO
from app.domains.search.interfaces.dtos import (
    CandidatePageDTO,
    RecordType,
    SearchCandidate,
)
from app.domains.search.services.search_service import SearchService

NOW = datetime(2026, 9, 30, tzinfo=UTC)


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
class _Port:
    """A record type that matches its titles by word, and by meaning only
    when handed a vector."""

    record_type: RecordType
    titles: list[str]
    calls: list[tuple[tuple[str, ...], bool]] = field(default_factory=list)
    word_pass_started: asyncio.Event = field(default_factory=asyncio.Event)

    async def search_candidates(
        self,
        *,
        user_id: uuid.UUID,
        terms: Sequence[str],
        query_embedding: Sequence[float] | None,
        max_distance: float,
        limit: int,
    ) -> CandidatePageDTO:
        self.calls.append((tuple(terms), query_embedding is not None))
        self.word_pass_started.set()
        candidates = []
        for title in self.titles:
            words = set(title.lower().split())
            has_word = any(term in words for term in terms)
            if has_word or query_embedding is not None:
                task = _task(title=title)
                candidates.append(
                    SearchCandidate(
                        record_type=self.record_type,
                        record_id=task.id,
                        item=task,
                        all_terms=all(term in words for term in terms) and has_word,
                        word_rank=0.5 if has_word else None,
                        distance=0.2 if query_embedding is not None else None,
                    )
                )
        return CandidatePageDTO(candidates=candidates, total=len(candidates))

    async def embedding_of(
        self, *, user_id: uuid.UUID, record_id: uuid.UUID
    ) -> tuple[float, ...] | None:
        return None


@dataclass
class _Embedder:
    vector: tuple[float, ...] | None
    wait_for: asyncio.Event | None = None

    async def embed_query(
        self, *, user_id: uuid.UUID, text: str
    ) -> tuple[float, ...] | None:
        if self.wait_for is not None:
            # Only returns once the word pass has begun: proves the two overlap.
            await asyncio.wait_for(self.wait_for.wait(), timeout=1)
        return self.vector


@dataclass
class _Analytics:
    runs: int = 0

    async def record_search_run(self, *, user_id: uuid.UUID) -> None:
        self.runs += 1


async def test_without_a_vector_word_matches_return_flagged_incomplete() -> None:
    """C-4, FR-20."""
    port = _Port(record_type=RecordType.TASK, titles=["Renew passport", "Buy milk"])
    analytics = _Analytics()
    service = SearchService(
        search_ports=[port], query_embedding=_Embedder(vector=None), analytics=analytics
    )

    results = await service.search_for_capture(user_id=uuid.uuid4(), text="passport")

    assert results.meaning_unavailable is True
    assert [hit.item.title for hit in results.groups[0].hits] == ["Renew passport"]
    assert port.calls == [(("passport",), False)]
    assert analytics.runs == 1


async def test_with_a_vector_a_second_pass_matches_by_meaning_too() -> None:
    port = _Port(record_type=RecordType.TASK, titles=["Renew passport", "Buy milk"])
    service = SearchService(
        search_ports=[port],
        query_embedding=_Embedder(vector=(0.1,) * 768),
        analytics=_Analytics(),
    )

    results = await service.search_for_capture(user_id=uuid.uuid4(), text="passport")

    assert results.meaning_unavailable is False
    assert [hit.item.title for hit in results.groups[0].hits] == [
        "Renew passport",
        "Buy milk",
    ]
    assert port.calls == [(("passport",), False), (("passport",), True)]


async def test_the_embed_and_the_word_pass_run_together() -> None:
    """C-4b, AD-4: the embed only finishes after the word pass has started,
    which deadlocks, and times out, if the two ran one after the other."""
    port = _Port(record_type=RecordType.TASK, titles=["Renew passport"])
    service = SearchService(
        search_ports=[port],
        query_embedding=_Embedder(vector=(0.1,) * 768, wait_for=port.word_pass_started),
        analytics=_Analytics(),
    )

    results = await service.search_for_capture(user_id=uuid.uuid4(), text="passport")

    assert results.meaning_unavailable is False


async def test_the_query_text_is_kept_as_typed() -> None:
    service = SearchService(
        search_ports=[_Port(record_type=RecordType.TASK, titles=[])],
        query_embedding=_Embedder(vector=None),
        analytics=_Analytics(),
    )

    results = await service.search_for_capture(
        user_id=uuid.uuid4(), text="When does my Passport expire?"
    )

    assert results.query == "When does my Passport expire?"
    assert results.groups == []


def test_every_record_type_has_a_search_port() -> None:
    """C-12, AD-11, FR-11: the wiring in core/deps.py reaches every type. A
    new record type added to RecordType without a port fails here."""
    from app.core.deps import build_search_service

    class _Context:
        session = None
        session_factory = None

    service = build_search_service(_Context())  # type: ignore[arg-type]

    assert service.covered_record_types == set(RecordType)
