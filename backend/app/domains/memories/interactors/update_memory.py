"""FR-18: edit a memory's text and category. FR-14: never a conflict check."""

import structlog

from app.domains.memories.constants import MAX_FACT_LENGTH
from app.domains.memories.graphql.errors import (
    InvalidMemoryError,
    MemoryNotFoundError,
    MemoryTooLongError,
)
from app.domains.memories.interactors.dtos import UpdateMemoryInputDTO
from app.domains.memories.interfaces.dtos import MemoryDTO
from app.domains.memories.interfaces.ports import MemoryAnalyticsPort, ReembedQueue
from app.domains.memories.interfaces.repositories import MemoryRepository

logger = structlog.get_logger(__name__)


class UpdateMemoryInteractor:
    def __init__(
        self,
        *,
        memory_repository: MemoryRepository,
        reembed_queue: ReembedQueue,
        analytics: MemoryAnalyticsPort,
    ) -> None:
        self.memory_repository = memory_repository
        self.reembed_queue = reembed_queue
        self.analytics = analytics

    async def update_memory(self, *, dto: UpdateMemoryInputDTO) -> MemoryDTO:
        """Replace the text and category of one live memory.

        Editing the text leaves the category as submitted; nothing reclassifies
        it (FR-18). The vector is refreshed by a job, so an edit never waits on
        the model.

        Raises:
            InvalidMemoryError: the text is empty.
            MemoryTooLongError: the text is over the limit.
            MemoryNotFoundError: no live memory with this id is theirs.
        """
        text = dto.text.strip()
        self._validate_text_present(text=text)
        self._validate_text_length(text=text)
        previous = await self.memory_repository.get_by_id(
            user_id=dto.user_id, memory_id=dto.memory_id
        )
        updated = await self.memory_repository.update_text_and_category(
            user_id=dto.user_id,
            memory_id=dto.memory_id,
            text=text,
            category=dto.category,
        )
        if previous is None or updated is None:
            raise MemoryNotFoundError()
        await self.reembed_queue.enqueue_reembed(
            user_id=dto.user_id, memory_id=dto.memory_id
        )
        if previous.category != updated.category:
            await self._record_category_edited(dto=dto)
        return updated

    def _validate_text_present(self, *, text: str) -> None:
        if not text:
            raise InvalidMemoryError(message="A memory needs some text.")

    def _validate_text_length(self, *, text: str) -> None:
        if len(text) > MAX_FACT_LENGTH:
            raise MemoryTooLongError(length=len(text))

    async def _record_category_edited(self, *, dto: UpdateMemoryInputDTO) -> None:
        """The PRD's category-trust metric. Never fails the edit."""
        try:
            await self.analytics.record_memory_event(
                user_id=dto.user_id, event_type="memory_category_edited"
            )
        except Exception:
            # Broad on purpose: an instrumentation loss is logged, never raised.
            logger.exception("memories.event_not_recorded", user_id=str(dto.user_id))
