"""Epic 005, sub-plan 4.1, C-4, C-4b and C-12: the search service's fallback,
its parallel embed, and its coverage of every record type (FR-11, FR-20,
AD-4, AD-11)."""

import asyncio
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime

from app.domains.records.public import TaskDTO
from app.domains.search.interfaces.dtos import (
    AnswerDraftDTO,
    AnswerRecordDTO,
    AnswerRefusedDTO,
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
        text: str,
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
    properties: list[dict[str, int | float | bool]] = field(default_factory=list)

    async def record_search_event(
        self,
        *,
        user_id: uuid.UUID,
        event_type: str,
        properties: dict[str, int | float | bool],
    ) -> None:
        self.runs += 1
        self.properties.append(properties)


@dataclass
class _Answerer:
    """Cites the records it is told to, or refuses as the gateway would."""

    draft: AnswerDraftDTO | AnswerRefusedDTO = field(
        default_factory=lambda: AnswerRefusedDTO(limit_reached=False)
    )
    calls: list[tuple[str, list[AnswerRecordDTO]]] = field(default_factory=list)

    async def write_answer(
        self,
        *,
        user_id: uuid.UUID,
        question: str,
        today: date,
        records: Sequence[AnswerRecordDTO],
    ) -> AnswerDraftDTO | AnswerRefusedDTO:
        self.calls.append((question, list(records)))
        return self.draft


@dataclass
class _Timezone:
    async def get_user_timezone(self, *, user_id: uuid.UUID) -> str:
        return "Asia/Kolkata"


def _service(
    *,
    ports: list[_Port],
    embedder: "_Embedder",
    analytics: "_Analytics | None" = None,
    answerer: _Answerer | None = None,
) -> SearchService:
    return SearchService(
        search_ports=ports,
        query_embedding=embedder,
        answer=answerer or _Answerer(),
        user_timezone=_Timezone(),
        analytics=analytics or _Analytics(),
        now_provider=lambda: NOW,
    )


async def test_without_a_vector_word_matches_return_flagged_incomplete() -> None:
    """C-4, FR-20."""
    port = _Port(record_type=RecordType.TASK, titles=["Renew passport", "Buy milk"])
    analytics = _Analytics()
    service = _service(
        ports=[port], embedder=_Embedder(vector=None), analytics=analytics
    )

    results = await service.search_for_capture(user_id=uuid.uuid4(), text="passport")

    assert results.meaning_unavailable is True
    assert [hit.item.title for hit in results.groups[0].hits] == ["Renew passport"]
    assert port.calls == [(("passport",), False)]
    assert analytics.runs == 1


async def test_with_a_vector_a_second_pass_matches_by_meaning_too() -> None:
    port = _Port(record_type=RecordType.TASK, titles=["Renew passport", "Buy milk"])
    service = _service(ports=[port], embedder=_Embedder(vector=(0.1,) * 768))

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
    service = _service(
        ports=[port],
        embedder=_Embedder(vector=(0.1,) * 768, wait_for=port.word_pass_started),
    )

    results = await service.search_for_capture(user_id=uuid.uuid4(), text="passport")

    assert results.meaning_unavailable is False


async def test_the_query_text_is_kept_as_typed() -> None:
    service = _service(
        ports=[_Port(record_type=RecordType.TASK, titles=[])],
        embedder=_Embedder(vector=None),
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


async def test_a_word_search_never_asks_for_an_answer() -> None:
    """C-2.6, FR-15."""
    answerer = _Answerer(draft=AnswerDraftDTO(sentences=[("x", [1])], supported=True))
    service = _service(
        ports=[_Port(record_type=RecordType.TASK, titles=["Renew passport"])],
        embedder=_Embedder(vector=None),
        answerer=answerer,
    )

    results = await service.search_for_capture(user_id=uuid.uuid4(), text="passport")

    assert answerer.calls == []
    assert results.answer is None
    assert results.no_support is False


async def test_a_question_gets_a_cited_answer_with_its_row_marked() -> None:
    """FR-16, FR-17: the top ten go to the model; the cited row carries [1]."""
    answerer = _Answerer(
        draft=AnswerDraftDTO(
            sentences=[("Your passport needs renewing.", [1])], supported=True
        )
    )
    analytics = _Analytics()
    service = _service(
        ports=[_Port(record_type=RecordType.TASK, titles=["Renew passport"])],
        embedder=_Embedder(vector=None),
        answerer=answerer,
        analytics=analytics,
    )

    results = await service.search_for_capture(
        user_id=uuid.uuid4(), text="When is my passport due?"
    )

    assert results.answer is not None
    assert results.answer.sentences[0].citations == [1]
    assert results.groups[0].hits[0].citation == 1
    question, records = answerer.calls[0]
    assert question == "When is my passport due?"
    assert [(record.number, record.text) for record in records] == [
        (1, "Renew passport")
    ]
    assert analytics.properties[0]["answered"] is True
    assert analytics.properties[0]["is_question"] is True


async def test_a_failed_answer_keeps_the_records() -> None:
    """C-2.7, FR-19."""
    service = _service(
        ports=[_Port(record_type=RecordType.TASK, titles=["Renew passport"])],
        embedder=_Embedder(vector=None),
        answerer=_Answerer(draft=AnswerRefusedDTO(limit_reached=False)),
    )

    results = await service.search_for_capture(
        user_id=uuid.uuid4(), text="when does my passport expire"
    )

    assert results.answer_unavailable is True
    assert results.answer_limit_reached is False
    assert results.answer is None
    assert results.groups[0].hits[0].item.title == "Renew passport"


async def test_an_answer_refused_for_the_daily_limit_says_so() -> None:
    """Q7: the card names the daily limit, not an outage."""
    service = _service(
        ports=[_Port(record_type=RecordType.TASK, titles=["Renew passport"])],
        embedder=_Embedder(vector=None),
        answerer=_Answerer(draft=AnswerRefusedDTO(limit_reached=True)),
    )

    results = await service.search_for_capture(
        user_id=uuid.uuid4(), text="when does my passport expire"
    )

    assert results.answer_unavailable is True
    assert results.answer_limit_reached is True
    assert results.groups[0].hits[0].item.title == "Renew passport"


async def test_a_question_with_no_records_says_so_without_a_model_call() -> None:
    """FR-18: nothing to read means nothing supports an answer."""
    answerer = _Answerer(draft=AnswerDraftDTO(sentences=[], supported=False))
    service = _service(
        ports=[_Port(record_type=RecordType.TASK, titles=[])],
        embedder=_Embedder(vector=None),
        answerer=answerer,
    )

    results = await service.search_for_capture(
        user_id=uuid.uuid4(), text="what is my blood type?"
    )

    assert results.no_support is True
    assert answerer.calls == []


async def test_a_records_page_ranks_across_types_and_pages_by_offset() -> None:
    """Sub-plan 4.3, C-3.1, FR-22: best match first across types; the second
    page continues where the first stopped; totals are the ports' own."""
    tasks = _Port(
        record_type=RecordType.TASK,
        titles=["career move", "career fair", "buy milk"],
    )
    memories = _Port(record_type=RecordType.MEMORY, titles=["career goal"])
    service = _service(ports=[tasks, memories], embedder=_Embedder(vector=None))

    first = await service.search_page(
        user_id=uuid.uuid4(), text="career", record_type=None, offset=0, limit=2
    )
    second = await service.search_page(
        user_id=uuid.uuid4(), text="career", record_type=None, offset=2, limit=2
    )

    assert [hit.item.title for hit in first.hits] == ["career move", "career fair"]
    assert [hit.item.title for hit in second.hits] == ["career goal"]
    assert first.total == 3
    assert first.other_types_total == 0
    assert first.meaning_unavailable is True
    assert all(hit.citation is None for hit in first.hits)


async def test_a_records_page_filters_to_a_type_and_counts_the_rest() -> None:
    """C-3.1: the filtered-no-match state needs the other types' count."""
    tasks = _Port(record_type=RecordType.TASK, titles=["career move", "career fair"])
    reminders = _Port(record_type=RecordType.REMINDER, titles=["buy milk"])
    service = _service(ports=[tasks, reminders], embedder=_Embedder(vector=None))

    page = await service.search_page(
        user_id=uuid.uuid4(),
        text="career",
        record_type=RecordType.REMINDER,
        offset=0,
        limit=50,
    )

    assert page.hits == []
    assert page.total == 0
    assert page.other_types_total == 2


async def test_a_records_page_never_writes_an_answer() -> None:
    """FR-22: a question typed into the records view is only searched."""
    answerer = _Answerer()
    analytics = _Analytics()
    port = _Port(record_type=RecordType.TASK, titles=["when is rent due"])
    service = _service(
        ports=[port],
        embedder=_Embedder(vector=None),
        answerer=answerer,
        analytics=analytics,
    )

    await service.search_page(
        user_id=uuid.uuid4(),
        text="when is rent due?",
        record_type=None,
        offset=0,
        limit=50,
    )

    assert answerer.calls == []
    assert analytics.runs == 0
