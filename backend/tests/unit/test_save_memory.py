"""MemoryService, sub-plan 4.1 cases C-2, C-4, C-5, C-6 and the FR-8 event."""

import uuid

from app.domains.gateway.public import ProviderUnavailable, SharedQuotaExhausted
from app.domains.memories.interfaces.dtos import (
    MemoryCategory,
    MemorySavedDTO,
    MemoryTooLongDTO,
    ModelRefused,
    SecretKind,
)
from app.domains.memories.services.memory_service import MemoryService
from tests.fakes.fake_memory_repository import (
    FakeMemoryAnalytics,
    FakeMemoryModel,
    FakeMemoryRepository,
)

USER = uuid.uuid4()


def _service(
    *, model: FakeMemoryModel | None = None
) -> tuple[MemoryService, FakeMemoryRepository, FakeMemoryModel, FakeMemoryAnalytics]:
    repository = FakeMemoryRepository()
    memory_model = model or FakeMemoryModel()
    analytics = FakeMemoryAnalytics()
    service = MemoryService(
        memory_repository=repository,
        embedding=memory_model,
        judgement=memory_model,
        analytics=analytics,
    )
    return service, repository, memory_model, analytics


async def test_the_fact_is_stored_as_typed_trimmed() -> None:
    """C-2, FR-2: the user's words, never the model's."""
    service, repository, _, analytics = _service()

    outcome = await service.save_memory(
        user_id=USER,
        text="  My passport expires in 2030 ",
        original_input="/remember   My passport expires in 2030",
    )

    assert isinstance(outcome, MemorySavedDTO)
    assert outcome.memory.text == "My passport expires in 2030"
    assert outcome.memory.category == MemoryCategory.LIFE
    assert outcome.secret_caution is None
    assert list(repository.rows) == [outcome.memory.id]
    assert repository.embeddings[outcome.memory.id] == (0.1, 0.2, 0.3)
    assert analytics.events == ["memory_saved"]


async def test_no_category_saves_uncategorised() -> None:
    """C-5, FR-6: the model's "none" never blocks or questions the save."""
    service, _, _, _ = _service(model=FakeMemoryModel(category=None))

    outcome = await service.save_memory(
        user_id=USER, text="Netflix renews on the 3rd", original_input="/remember x"
    )

    assert isinstance(outcome, MemorySavedDTO)
    assert outcome.memory.category is None


async def test_an_over_long_fact_is_refused_before_any_model_call() -> None:
    """C-4, FR-4."""
    service, repository, memory_model, _ = _service()

    outcome = await service.save_memory(
        user_id=USER, text="x" * 501, original_input="/remember ..."
    )

    assert outcome == MemoryTooLongDTO(length=501)
    assert repository.rows == {}
    assert memory_model.embedded_texts == []
    assert memory_model.judged_texts == []


async def test_exactly_500_characters_is_allowed() -> None:
    service, _, _, _ = _service()

    outcome = await service.save_memory(
        user_id=USER, text="x" * 500, original_input="/remember ..."
    )

    assert isinstance(outcome, MemorySavedDTO)


async def test_an_embed_failure_writes_nothing() -> None:
    """C-6, FR-9: the refusal is carried out unchanged, and no row exists."""
    refusal = ProviderUnavailable(message="down")
    service, repository, memory_model, analytics = _service(
        model=FakeMemoryModel(embed_refusal=refusal)
    )

    outcome = await service.save_memory(
        user_id=USER, text="Car insurance renews in March", original_input="/remember"
    )

    assert outcome == ModelRefused(gateway_result=refusal)
    assert repository.rows == {}
    assert memory_model.judged_texts == []
    assert analytics.events == []


async def test_a_judgement_failure_writes_nothing() -> None:
    """C-6, FR-9: a vector alone is never saved."""
    refusal = SharedQuotaExhausted(message="busy")
    service, repository, _, _ = _service(model=FakeMemoryModel(judge_refusal=refusal))

    outcome = await service.save_memory(
        user_id=USER, text="Car insurance renews in March", original_input="/remember"
    )

    assert outcome == ModelRefused(gateway_result=refusal)
    assert repository.rows == {}


async def test_a_secret_saves_with_its_caution_and_event() -> None:
    """FR-8: warns, never blocks, and the caution names the kind only."""
    service, repository, _, analytics = _service()

    outcome = await service.save_memory(
        user_id=USER, text="Locker PIN is 4417", original_input="/remember ..."
    )

    assert isinstance(outcome, MemorySavedDTO)
    assert outcome.secret_caution == SecretKind.CREDENTIAL
    assert len(repository.rows) == 1
    assert analytics.events == ["memory_saved", "memory_secret_caution"]


async def test_lookup_finds_by_word_and_says_what_it_searched() -> None:
    """FR-20, with the fake repository's word matching."""
    service, _, _, analytics = _service()
    await service.save_memory(
        user_id=USER, text="Career goal: backend engineer", original_input="/remember"
    )
    await service.save_memory(
        user_id=USER, text="Mom's birthday is October 12", original_input="/remember"
    )

    found = await service.look_up_memories(user_id=USER, text="my career")

    assert [memory.text for memory in found.memories] == [
        "Career goal: backend engineer"
    ]
    assert found.search_text == "my career"
    assert analytics.events[-1] == "memory_lookup"
