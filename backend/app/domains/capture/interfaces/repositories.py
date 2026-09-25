"""The contract for pending-capture and capture-turn storage."""

from typing import Protocol
from uuid import UUID

from app.domains.capture.interfaces.dtos import (
    CaptureHistoryPageDTO,
    CaptureTurnOutcome,
    MissingField,
    PendingCaptureDTO,
)


class PendingCaptureRepository(Protocol):
    async def create_pending_capture(
        self,
        *,
        user_id: UUID,
        command_name: str,
        known_title: str | None,
        missing_field: MissingField,
        question_text: str,
        original_input: str,
    ) -> PendingCaptureDTO: ...

    async def get_pending_capture(
        self, *, user_id: UUID, pending_capture_id: UUID
    ) -> PendingCaptureDTO | None: ...

    async def delete_pending_capture(
        self, *, user_id: UUID, pending_capture_id: UUID
    ) -> None: ...


class CaptureTurnRepository(Protocol):
    async def record_turn(
        self,
        *,
        user_id: UUID,
        input_text: str,
        outcome: CaptureTurnOutcome,
        resulting_task_id: UUID | None,
        resulting_pending_capture_id: UUID | None,
        question_text: str | None,
        answer_text: str | None,
        resulting_reminder_id: UUID | None = None,
        resulting_memory_id: UUID | None = None,
        affected_count: int | None = None,
    ) -> None: ...

    async def scrub_turns_for_memories(
        self, *, user_id: UUID, memory_ids: list[UUID]
    ) -> int:
        """FR-23: blank every turn that saved one of these memories."""
        ...

    async def list_turns_for_user(
        self, *, user_id: UUID, cursor: str | None, limit: int
    ) -> CaptureHistoryPageDTO: ...
