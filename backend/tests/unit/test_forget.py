"""MemoryService forget, sub-plan 4.2 cases C-2.4 to C-2.7, C-2.11 and C-2.12."""

import uuid

import pytest

from app.domains.memories.interfaces.dtos import (
    MemoriesForgottenDTO,
    MemoryCategory,
    MemoryCountChangedDTO,
    MemoryDTO,
)
from app.domains.memories.interfaces.repositories import MemoryWrite
from app.domains.memories.services.memory_service import MemoryService
from tests.fakes.fake_memory_repository import (
    FakeMemoryAnalytics,
    FakeMemoryModel,
    FakeMemoryRepository,
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
        self.service = MemoryService(
            memory_repository=self.repository,
            embedding=self.model,
            judgement=self.model,
            analytics=self.analytics,
            turn_scrub=self.scrub,
        )

    async def seed(self, text: str, *, user_id: uuid.UUID = USER) -> MemoryDTO:
        return await self.repository.create_memory(
            user_id=user_id,
            write=MemoryWrite(
                text=text,
                category=MemoryCategory.LIFE,
                embedding=(1.0,),
                origin="command",
                original_input=f"/remember {text}",
            ),
        )


async def test_forget_scrubs_history_before_the_tombstone() -> None:
    """Sub-plan 4.2 §5: the scrub sees the memory still live."""
    harness = Harness()
    memory = await harness.seed("Preferred airline is Emirates")

    forgotten = await harness.service.forget_memories(
        user_id=USER, memory_ids=[memory.id]
    )

    assert forgotten == MemoriesForgottenDTO(count=1)
    assert harness.scrub.scrubbed == [memory.id]
    assert harness.scrub.live_when_scrubbed == [True]
    assert harness.repository.forgotten_ids == [memory.id]


async def test_a_failed_tombstone_leaves_the_memory_live_and_a_retry_finishes() -> None:
    """C-2.11."""
    harness = Harness()
    memory = await harness.seed("Locker PIN 4417")
    harness.repository.tombstone_should_fail = True

    with pytest.raises(RuntimeError):
        await harness.service.forget_memories(user_id=USER, memory_ids=[memory.id])
    assert memory.id in harness.repository.rows

    harness.repository.tombstone_should_fail = False
    retried = await harness.service.forget_memories(
        user_id=USER, memory_ids=[memory.id]
    )

    assert retried.count == 1
    assert memory.id not in harness.repository.rows


async def test_another_users_ids_forget_nothing() -> None:
    """C-2.10 at the service: nothing scrubbed, nothing tombstoned."""
    harness = Harness()
    theirs = await harness.seed("Theirs", user_id=OTHER_USER)

    forgotten = await harness.service.forget_memories(
        user_id=USER, memory_ids=[theirs.id]
    )

    assert forgotten.count == 0
    assert harness.scrub.scrubbed == []
    assert theirs.id in harness.repository.rows


async def test_candidates_are_capped_at_five_with_the_true_total() -> None:
    """C-2.4, Q2."""
    harness = Harness()
    for number in range(7):
        await harness.seed(f"Airline note {number}")
    await harness.seed("Mom's birthday is October 12")

    offered = await harness.service.find_forget_candidates(user_id=USER, text="airline")

    assert len(offered.candidates) == 5
    assert offered.total_matches == 7
    assert offered.forget_all is False


async def test_no_match_offers_nothing() -> None:
    """C-2.5."""
    harness = Harness()
    await harness.seed("Mom's birthday is October 12")

    offered = await harness.service.find_forget_candidates(user_id=USER, text="visa")

    assert offered.candidates == []
    assert offered.total_matches == 0
    assert harness.scrub.scrubbed == []


@pytest.mark.parametrize("phrase", ["all", "everything", "all my memories", " ALL "])
async def test_exact_phrases_offer_forget_all_with_the_count(phrase: str) -> None:
    """C-2.6, Q4."""
    harness = Harness()
    await harness.seed("One")
    await harness.seed("Two")

    offered = await harness.service.find_forget_candidates(user_id=USER, text=phrase)

    assert offered.forget_all is True
    assert offered.all_count == 2


async def test_all_inside_other_words_is_a_word_match() -> None:
    """C-2.6: `/forget all receipts` never starts a forget-all."""
    harness = Harness()
    await harness.seed("Keep all receipts for the car")

    offered = await harness.service.find_forget_candidates(
        user_id=USER, text="all receipts"
    )

    assert offered.forget_all is False
    assert len(offered.candidates) == 1


async def test_forget_all_refuses_a_stale_count() -> None:
    """C-2.7."""
    harness = Harness()
    await harness.seed("One")
    await harness.seed("Two")

    stale = await harness.service.forget_all(user_id=USER, expected_count=1)
    confirmed = await harness.service.forget_all(user_id=USER, expected_count=2)

    assert stale == MemoryCountChangedDTO(count=2)
    assert confirmed == MemoriesForgottenDTO(count=2)
    assert harness.repository.rows == {}


async def test_forget_never_calls_the_model_and_records_one_textless_event() -> None:
    """C-2.12."""
    harness = Harness()
    memory = await harness.seed("My passport number is P1234567")

    await harness.service.forget_memories(user_id=USER, memory_ids=[memory.id])

    assert harness.model.embedded_texts == []
    assert harness.model.judged_texts == []
    assert harness.analytics.events == ["memory_forgotten"]
