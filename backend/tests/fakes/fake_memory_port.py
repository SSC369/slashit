"""In-memory stand-ins for capture's MemoryPort and records' MemoryRecordsPort."""

import uuid
from datetime import UTC, datetime
from uuid import UUID

from app.domains.capture.interfaces.ports import MemorySaveOutcome
from app.domains.memories.public import (
    ForgetCandidatesDTO,
    MemoriesForgottenDTO,
    MemoryCountChangedDTO,
    MemoryDTO,
    MemoryListDTO,
    MemorySavedDTO,
    MemoryTooLongDTO,
)


def make_memory(
    *, user_id: UUID, text: str, created_at: datetime | None = None
) -> MemoryDTO:
    moment = created_at or datetime.now(UTC)
    return MemoryDTO(
        id=uuid.uuid4(),
        user_id=user_id,
        text=text,
        category=None,
        origin="command",
        original_input=f"/remember {text}",
        created_at=moment,
        updated_at=moment,
    )


class FakeMemoryPort:
    """Saves into a list; returns ``refusal`` instead when one is set."""

    def __init__(self, *, refusal: MemorySaveOutcome | None = None) -> None:
        self.refusal = refusal
        self.saved: list[MemoryDTO] = []
        self.lookups: list[str] = []
        self.forgotten: list[UUID] = []

    async def save_memory(
        self, *, user_id: UUID, text: str, original_input: str
    ) -> MemorySaveOutcome:
        if self.refusal is not None:
            return self.refusal
        if len(text) > 500:
            return MemoryTooLongDTO(length=len(text))
        memory = make_memory(user_id=user_id, text=text)
        self.saved.append(memory)
        return MemorySavedDTO(memory=memory, secret_caution=None)

    async def list_memories(self, *, user_id: UUID) -> MemoryListDTO:
        return MemoryListDTO(
            memories=[memory for memory in self.saved if memory.user_id == user_id],
            search_text=None,
        )

    async def look_up_memories(self, *, user_id: UUID, text: str) -> MemoryListDTO:
        self.lookups.append(text)
        return MemoryListDTO(memories=[], search_text=text)

    async def find_forget_candidates(
        self, *, user_id: UUID, text: str
    ) -> ForgetCandidatesDTO:
        matches = [
            memory
            for memory in self.saved
            if memory.user_id == user_id
            and text
            and text.lower() in memory.text.lower()
        ]
        return ForgetCandidatesDTO(
            search_text=text,
            candidates=matches[:5],
            total_matches=len(matches),
            forget_all=text.lower() == "all",
            all_count=len(self.saved) if text.lower() == "all" else 0,
        )

    async def forget_memories(
        self, *, user_id: UUID, memory_ids: list[UUID]
    ) -> MemoriesForgottenDTO:
        live = [memory for memory in self.saved if memory.id in memory_ids]
        self.saved = [memory for memory in self.saved if memory.id not in memory_ids]
        self.forgotten.extend(memory.id for memory in live)
        return MemoriesForgottenDTO(count=len(live))

    async def forget_all(
        self, *, user_id: UUID, expected_count: int
    ) -> MemoriesForgottenDTO | MemoryCountChangedDTO:
        if len(self.saved) != expected_count:
            return MemoryCountChangedDTO(count=len(self.saved))
        return await self.forget_memories(
            user_id=user_id, memory_ids=[memory.id for memory in self.saved]
        )


class FakeMemoryRecordsPort:
    def __init__(self, memories: list[MemoryDTO] | None = None) -> None:
        self.memories = memories or []

    async def list_memories(
        self, *, user_id: UUID, search: str | None
    ) -> list[MemoryDTO]:
        return [
            memory
            for memory in self.memories
            if memory.user_id == user_id
            and (not search or search.lower() in memory.text.lower())
        ]
