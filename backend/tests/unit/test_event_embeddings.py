"""Epic 007, sub-plan 4.2, T-2.7: the embed job, its backfill, the embeds a
create and an edit queue, and an event's line in a written answer (C-16)."""

import uuid
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.domains.events.interactors.create_event import CreateEventInteractor
from app.domains.events.interactors.dtos import (
    CreateEventInputDTO,
    EmbedEventInputDTO,
    QueueMissingEventEmbeddingsInputDTO,
    UpdateEventInputDTO,
)
from app.domains.events.interactors.embed_event import (
    EmbedEventFailedError,
    EmbedEventInteractor,
)
from app.domains.events.interactors.queue_missing_event_embeddings import (
    QueueMissingEventEmbeddingsInteractor,
)
from app.domains.events.interactors.update_event import UpdateEventInteractor
from app.domains.events.interfaces.dtos import EventDTO, EventEdit, EventFields
from app.domains.search.interfaces.dtos import RecordType
from app.domains.search.services.answer_records import describe_record
from tests.fakes.fake_calendar_event_repository import FakeCalendarEventRepository
from tests.fakes.fake_event_ports import (
    FakeEventAnalyticsPort,
    FakeEventEmbedQueue,
    FakeEventUserClockPort,
    fake_alert_arming,
)

USER = uuid.uuid4()
KOLKATA = ZoneInfo("Asia/Kolkata")
NOW = datetime(2026, 10, 2, 10, 0, tzinfo=KOLKATA).astimezone(UTC)
VECTOR = (0.1, 0.2, 0.3)


class _Embedder:
    def __init__(self, *, vector: tuple[float, ...] | None) -> None:
        self.vector = vector
        self.texts: list[str] = []

    async def embed_event_text(
        self, *, user_id: uuid.UUID, text: str
    ) -> tuple[float, ...] | None:
        self.texts.append(text)
        return self.vector


class World:
    def __init__(self) -> None:
        self.repository = FakeCalendarEventRepository()
        self.queue = FakeEventEmbedQueue()
        self.clock = FakeEventUserClockPort()

    async def create(
        self, *, title: str = "Dentist", location: str | None = "Apollo Clinic"
    ) -> EventDTO:
        event = await CreateEventInteractor(
            event_repository=self.repository,
            user_clock=self.clock,
            alert_arming=fake_alert_arming(repository=self.repository),
            analytics=FakeEventAnalyticsPort(),
            embed_queue=self.queue,
            now_provider=lambda: NOW,
        ).create_event(
            dto=CreateEventInputDTO(
                user_id=USER,
                fields=EventFields(
                    title=title,
                    start_date=date(2026, 10, 9),
                    has_year=True,
                    start_time=time(16),
                    end_date=None,
                    end_time=None,
                    location=location,
                    description=None,
                    repeat_yearly=False,
                    alert_leads_minutes=(),
                ),
                origin="command",
                original_input=None,
            )
        )
        assert isinstance(event, EventDTO)
        return event

    async def edit(self, *, event: EventDTO, title: str, location: str | None) -> None:
        await UpdateEventInteractor(
            event_repository=self.repository,
            user_clock=self.clock,
            alert_arming=fake_alert_arming(repository=self.repository),
            embed_queue=self.queue,
            analytics=FakeEventAnalyticsPort(),
            now_provider=lambda: NOW,
        ).update_event(
            dto=UpdateEventInputDTO(
                user_id=USER,
                event_id=event.id,
                edit=EventEdit(
                    title=title,
                    location=location,
                    description=None,
                    start_date=date(2026, 10, 9),
                    start_time=time(16),
                    end_date=None,
                    end_time=None,
                    repeat_yearly=False,
                    alert_leads_minutes=(),
                ),
            )
        )

    def embed(self, *, embedder: _Embedder) -> EmbedEventInteractor:
        return EmbedEventInteractor(
            event_repository=self.repository, embedding=embedder
        )


async def test_a_create_queues_one_embed() -> None:
    """005 AD-7: a new event is searchable by meaning once the job runs."""
    world = World()
    event = await world.create()
    assert world.queue.queued == [(USER, event.id, 0)]


async def test_an_edit_queues_an_embed_only_when_the_words_change() -> None:
    world = World()
    event = await world.create()
    world.queue.queued.clear()

    await world.edit(event=event, title="Dentist", location="Apollo Clinic")
    assert world.queue.queued == []

    await world.edit(event=event, title="Dentist", location="Indiranagar")
    assert world.queue.queued == [(USER, event.id, 0)]


async def test_the_job_embeds_title_location_and_description_once() -> None:
    """C-16: the vector is made from the event's words, and stored once."""
    world = World()
    event = await world.create()
    embedder = _Embedder(vector=VECTOR)

    first = await world.embed(embedder=embedder).embed_event(
        dto=EmbedEventInputDTO(user_id=USER, event_id=event.id)
    )
    second = await world.embed(embedder=embedder).embed_event(
        dto=EmbedEventInputDTO(user_id=USER, event_id=event.id)
    )

    assert (first, second) == (True, False)
    assert embedder.texts == ["Dentist · Apollo Clinic"]
    assert world.repository.embeddings[event.id] == VECTOR


async def test_a_word_edit_clears_the_vector_for_the_next_embed() -> None:
    world = World()
    event = await world.create()
    await world.embed(embedder=_Embedder(vector=VECTOR)).embed_event(
        dto=EmbedEventInputDTO(user_id=USER, event_id=event.id)
    )

    await world.edit(event=event, title="Dentist checkup", location=None)

    assert event.id not in world.repository.embeddings


async def test_a_refused_embed_raises_for_the_retry() -> None:
    world = World()
    event = await world.create()

    with pytest.raises(EmbedEventFailedError):
        await world.embed(embedder=_Embedder(vector=None)).embed_event(
            dto=EmbedEventInputDTO(user_id=USER, event_id=event.id)
        )


async def test_the_backfill_queues_recent_events_and_every_one_when_full() -> None:
    world = World()
    first = await world.create(title="Dentist")
    second = await world.create(title="Flight")
    world.queue.queued.clear()
    backfill = QueueMissingEventEmbeddingsInteractor(
        event_repository=world.repository,
        embed_queue=world.queue,
        now_provider=lambda: datetime.now(UTC) + timedelta(days=2),
    )

    recent = await backfill.queue_missing_event_embeddings(
        dto=QueueMissingEventEmbeddingsInputDTO(full=False)
    )
    full = await backfill.queue_missing_event_embeddings(
        dto=QueueMissingEventEmbeddingsInputDTO(full=True)
    )

    assert (recent, full) == (0, 2)
    assert {event_id for _, event_id, _ in world.queue.queued} == {first.id, second.id}


async def test_an_answer_can_cite_an_event() -> None:
    """005 FR-16 and FR-17 for events: when, repeat and place in one line."""
    world = World()
    event = await world.create()

    line = describe_record(
        number=1, record_type=RecordType.EVENT, item=event, timezone=KOLKATA
    )

    assert line.text == "Dentist"
    assert line.detail == "event, Fri 9 Oct, 4:00 PM, at Apollo Clinic"
