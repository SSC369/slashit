"""Records-side memory use cases, sub-plan 4.1 cases C-9 and C-10."""

import uuid

import pytest

from app.domains.gateway.public import ProviderTimeout
from app.domains.memories.graphql.errors import (
    InvalidMemoryError,
    MemoryNotFoundError,
    MemoryTooLongError,
)
from app.domains.memories.interactors.dtos import (
    GetMemoryInputDTO,
    ListMemoriesInputDTO,
    ReembedMemoryInputDTO,
    UpdateMemoryInputDTO,
)
from app.domains.memories.interactors.get_memory import GetMemoryInteractor
from app.domains.memories.interactors.list_memories import ListMemoriesInteractor
from app.domains.memories.interactors.reembed_memory import (
    ReembedFailedError,
    ReembedMemoryInteractor,
)
from app.domains.memories.interactors.update_memory import UpdateMemoryInteractor
from app.domains.memories.interfaces.dtos import MemoryCategory, MemoryDTO
from app.domains.memories.interfaces.repositories import MemoryWrite
from tests.fakes.fake_memory_repository import (
    FakeMemoryAnalytics,
    FakeMemoryModel,
    FakeMemoryRepository,
    FakeReembedQueue,
)

USER = uuid.uuid4()
OTHER_USER = uuid.uuid4()


async def _seed(
    repository: FakeMemoryRepository,
    *,
    text: str,
    category: MemoryCategory | None,
    user_id: uuid.UUID = USER,
) -> MemoryDTO:
    return await repository.create_memory(
        user_id=user_id,
        write=MemoryWrite(
            text=text,
            category=category,
            embedding=(1.0,),
            origin="command",
            original_input=f"/remember {text}",
        ),
    )


def _update_interactor(
    repository: FakeMemoryRepository,
) -> tuple[UpdateMemoryInteractor, FakeReembedQueue, FakeMemoryAnalytics]:
    queue = FakeReembedQueue()
    analytics = FakeMemoryAnalytics()
    return (
        UpdateMemoryInteractor(
            memory_repository=repository, reembed_queue=queue, analytics=analytics
        ),
        queue,
        analytics,
    )


async def test_list_filters_by_category_and_by_uncategorised() -> None:
    """C-9, FR-16."""
    repository = FakeMemoryRepository()
    await _seed(repository, text="Mom's birthday", category=MemoryCategory.PEOPLE)
    await _seed(repository, text="Netflix renews", category=None)
    interactor = ListMemoriesInteractor(memory_repository=repository)

    people = await interactor.list_memories(
        dto=ListMemoriesInputDTO(
            user_id=USER, category=MemoryCategory.PEOPLE, search=None
        )
    )
    none = await interactor.list_memories(
        dto=ListMemoriesInputDTO(user_id=USER, category="uncategorised", search=" ")
    )

    assert [memory.text for memory in people] == ["Mom's birthday"]
    assert [memory.text for memory in none] == ["Netflix renews"]


async def test_edit_keeps_the_category_and_queues_a_reembed() -> None:
    """C-10, FR-18: the text changes, the category stays as submitted."""
    repository = FakeMemoryRepository()
    memory = await _seed(repository, text="Passport 2030", category=MemoryCategory.LIFE)
    interactor, queue, analytics = _update_interactor(repository)

    updated = await interactor.update_memory(
        dto=UpdateMemoryInputDTO(
            user_id=USER,
            memory_id=memory.id,
            text=" My passport expires in March 2030 ",
            category=MemoryCategory.LIFE,
        )
    )

    assert updated.text == "My passport expires in March 2030"
    assert updated.category == MemoryCategory.LIFE
    assert updated.origin == "edit"
    assert repository.embeddings[memory.id] is None
    assert queue.queued == [memory.id]
    assert analytics.events == []


async def test_a_category_change_records_its_event() -> None:
    repository = FakeMemoryRepository()
    memory = await _seed(repository, text="Learning Go", category=MemoryCategory.LIFE)
    interactor, _, analytics = _update_interactor(repository)

    await interactor.update_memory(
        dto=UpdateMemoryInputDTO(
            user_id=USER,
            memory_id=memory.id,
            text="Learning Go",
            category=MemoryCategory.PROFESSIONAL,
        )
    )

    assert analytics.events == ["memory_category_edited"]


@pytest.mark.parametrize(
    ("text", "error"),
    [("   ", InvalidMemoryError), ("x" * 501, MemoryTooLongError)],
)
async def test_edit_rejects_empty_and_over_long_text_before_writing(
    text: str, error: type[Exception]
) -> None:
    repository = FakeMemoryRepository()
    memory = await _seed(repository, text="Keep me", category=None)
    interactor, queue, _ = _update_interactor(repository)

    with pytest.raises(error):
        await interactor.update_memory(
            dto=UpdateMemoryInputDTO(
                user_id=USER, memory_id=memory.id, text=text, category=None
            )
        )

    assert repository.rows[memory.id].text == "Keep me"
    assert queue.queued == []


async def test_another_users_memory_reads_as_not_found() -> None:
    """NFR-1 at the interactor: get and edit both refuse."""
    repository = FakeMemoryRepository()
    memory = await _seed(repository, text="Theirs", category=None, user_id=OTHER_USER)
    interactor, _, _ = _update_interactor(repository)

    with pytest.raises(MemoryNotFoundError):
        await GetMemoryInteractor(memory_repository=repository).get_memory(
            dto=GetMemoryInputDTO(user_id=USER, memory_id=memory.id)
        )
    with pytest.raises(MemoryNotFoundError):
        await interactor.update_memory(
            dto=UpdateMemoryInputDTO(
                user_id=USER, memory_id=memory.id, text="Mine now", category=None
            )
        )
    assert repository.rows[memory.id].text == "Theirs"


async def test_reembed_stores_a_fresh_vector() -> None:
    repository = FakeMemoryRepository()
    memory = await _seed(repository, text="New text", category=None)
    repository.embeddings[memory.id] = None
    model = FakeMemoryModel()
    interactor = ReembedMemoryInteractor(memory_repository=repository, embedding=model)

    refreshed = await interactor.reembed_memory(
        dto=ReembedMemoryInputDTO(user_id=USER, memory_id=memory.id)
    )

    assert refreshed is True
    assert repository.embeddings[memory.id] == (0.1, 0.2, 0.3)
    assert model.embedded_texts == ["New text"]


async def test_reembed_raises_on_refusal_so_the_job_retries() -> None:
    repository = FakeMemoryRepository()
    memory = await _seed(repository, text="New text", category=None)
    interactor = ReembedMemoryInteractor(
        memory_repository=repository,
        embedding=FakeMemoryModel(
            embed_refusal=ProviderTimeout(message="slow", budget_seconds=3.0)
        ),
    )

    with pytest.raises(ReembedFailedError):
        await interactor.reembed_memory(
            dto=ReembedMemoryInputDTO(user_id=USER, memory_id=memory.id)
        )


async def test_reembed_of_a_missing_memory_is_a_quiet_no() -> None:
    interactor = ReembedMemoryInteractor(
        memory_repository=FakeMemoryRepository(), embedding=FakeMemoryModel()
    )

    refreshed = await interactor.reembed_memory(
        dto=ReembedMemoryInputDTO(user_id=USER, memory_id=uuid.uuid4())
    )

    assert refreshed is False
