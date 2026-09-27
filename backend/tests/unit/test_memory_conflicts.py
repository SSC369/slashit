"""MemoryService's conflict check and answers, sub-plan 4.3 cases C-3.1 to
C-3.4, C-3.7 and C-3.12 at the service."""

import uuid

from app.domains.memories.interfaces.dtos import (
    ConflictAnswer,
    MemoryCategory,
    MemoryConflictDTO,
    MemoryDiscardedDTO,
    MemoryDTO,
    MemorySavedDTO,
)
from app.domains.memories.interfaces.repositories import MemoryWrite
from app.domains.memories.services.memory_service import MemoryService
from tests.fakes.fake_memory_repository import (
    FakeMemoryAnalytics,
    FakeMemoryModel,
    FakeMemoryRepository,
    FakeReembedQueue,
    FakeTurnScrub,
)

USER = uuid.uuid4()
OTHER_USER = uuid.uuid4()


class Harness:
    def __init__(self) -> None:
        self.repository = FakeMemoryRepository()
        self.scrub = FakeTurnScrub(repository=self.repository)
        self.analytics = FakeMemoryAnalytics()
        self.model = FakeMemoryModel()
        self.queue = FakeReembedQueue()
        self.service = MemoryService(
            memory_repository=self.repository,
            embedding=self.model,
            judgement=self.model,
            analytics=self.analytics,
            turn_scrub=self.scrub,
            reembed_queue=self.queue,
        )

    async def seed(
        self,
        text: str,
        *,
        user_id: uuid.UUID = USER,
        embedding: tuple[float, ...] | None = (1.0,),
    ) -> MemoryDTO:
        return await self.repository.create_memory(
            user_id=user_id,
            write=MemoryWrite(
                text=text,
                category=MemoryCategory.PERSONAL,
                embedding=embedding,
                origin="command",
                original_input=f"/remember {text}",
            ),
        )

    async def resolve(
        self, *, conflicting: list[MemoryDTO], answer: ConflictAnswer
    ) -> MemorySavedDTO | MemoryDiscardedDTO:
        return await self.service.resolve_conflict(
            user_id=USER,
            text="My preferred airline is Qatar Airways",
            category=MemoryCategory.PERSONAL,
            original_input="/remember My preferred airline is Qatar Airways",
            conflicting_ids=[memory.id for memory in conflicting],
            answer=answer,
        )


async def test_a_contradiction_saves_nothing_and_names_the_old_memory() -> None:
    """C-3.1, FR-10."""
    harness = Harness()
    emirates = await harness.seed("Preferred airline is Emirates")
    harness.model.contradicts = {"Preferred airline is Emirates"}

    outcome = await harness.service.save_memory(
        user_id=USER,
        text="My preferred airline is Qatar Airways",
        original_input="/remember My preferred airline is Qatar Airways",
    )

    assert isinstance(outcome, MemoryConflictDTO)
    assert outcome.text == "My preferred airline is Qatar Airways"
    assert outcome.category is MemoryCategory.LIFE
    assert outcome.conflicting == [emirates]
    assert list(harness.repository.rows) == [emirates.id]
    assert "memory_saved" not in harness.analytics.events


async def test_candidates_are_the_nearest_ten_live_memories_with_a_vector() -> None:
    """C-3.2, FR-22, AD-5: forgotten, vectorless and other users' memories
    are never offered."""
    harness = Harness()
    for index in range(12):
        await harness.seed(f"Fact number {index}")
    unvectored = await harness.seed("Just edited, no vector yet", embedding=None)
    forgotten = await harness.seed("Old passport number")
    await harness.service.forget_memories(user_id=USER, memory_ids=[forgotten.id])
    await harness.seed("Someone else's fact", user_id=OTHER_USER)

    await harness.service.save_memory(
        user_id=USER, text="A new fact", original_input="/remember A new fact"
    )

    offered = harness.model.offered[-1]
    offered_ids = {candidate.id for candidate in offered}
    assert len(offered) == 10
    assert unvectored.id not in offered_ids
    assert forgotten.id not in offered_ids
    assert all("Someone else" not in candidate.text for candidate in offered)


async def test_keep_new_saves_it_and_forgets_the_old_one() -> None:
    """C-3.3, FR-11, FR-12."""
    harness = Harness()
    emirates = await harness.seed("Preferred airline is Emirates")

    outcome = await harness.resolve(
        conflicting=[emirates], answer=ConflictAnswer.KEEP_NEW
    )

    assert isinstance(outcome, MemorySavedDTO)
    assert outcome.memory.text == "My preferred airline is Qatar Airways"
    assert harness.repository.forgotten_ids == [emirates.id]
    assert harness.scrub.scrubbed == [emirates.id]


async def test_keep_old_saves_nothing_and_both_keeps_everything() -> None:
    """C-3.4, FR-11."""
    harness = Harness()
    emirates = await harness.seed("Preferred airline is Emirates")

    discarded = await harness.resolve(
        conflicting=[emirates], answer=ConflictAnswer.KEEP_OLD
    )
    assert isinstance(discarded, MemoryDiscardedDTO)
    assert list(harness.repository.rows) == [emirates.id]

    both = await harness.resolve(conflicting=[emirates], answer=ConflictAnswer.BOTH)
    assert isinstance(both, MemorySavedDTO)
    assert set(harness.repository.rows) == {emirates.id, both.memory.id}
    assert harness.repository.forgotten_ids == []


async def test_keep_new_forgets_only_memories_still_live() -> None:
    """C-3.7: one old memory was forgotten elsewhere before the answer."""
    harness = Harness()
    first = await harness.seed("Preferred airline is Emirates")
    second = await harness.seed("I only fly Emirates")
    await harness.service.forget_memories(user_id=USER, memory_ids=[first.id])

    outcome = await harness.resolve(
        conflicting=[first, second], answer=ConflictAnswer.KEEP_NEW
    )

    assert isinstance(outcome, MemorySavedDTO)
    assert harness.repository.forgotten_ids == [first.id, second.id]
    assert outcome.memory.id in harness.repository.rows


async def test_an_answer_never_calls_the_model_and_queues_the_vector() -> None:
    """C-3.12 and Q1: the saved memory waits for the reembed job."""
    harness = Harness()
    emirates = await harness.seed("Preferred airline is Emirates")

    outcome = await harness.resolve(conflicting=[emirates], answer=ConflictAnswer.BOTH)

    assert isinstance(outcome, MemorySavedDTO)
    assert harness.model.embedded_texts == []
    assert harness.model.judged_texts == []
    assert harness.repository.embeddings[outcome.memory.id] is None
    assert harness.queue.queued == [outcome.memory.id]
    assert harness.analytics.events[0] == "memory_conflict_answered"
