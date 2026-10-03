"""The contract for pending-capture and capture-turn storage."""

from typing import Protocol
from uuid import UUID

from app.domains.capture.interfaces.dtos import (
    CaptureHistoryPageDTO,
    CaptureTurnOutcome,
    ExpenseDraft,
    ExpenseQuestionKind,
    MissingField,
    PendingCaptureDTO,
)
from app.domains.memories.public import MemoryCategory


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

    async def create_pending_conflict(
        self,
        *,
        user_id: UUID,
        command_name: str,
        question_text: str,
        original_input: str,
        candidate_text: str,
        candidate_category: MemoryCategory | None,
        conflicting_memory_ids: list[UUID],
    ) -> PendingCaptureDTO: ...

    async def create_pending_expense(
        self,
        *,
        user_id: UUID,
        kind: ExpenseQuestionKind,
        question_text: str,
        original_input: str,
        draft: ExpenseDraft,
        date_words: str | None,
        replacing_id: UUID | None,
    ) -> PendingCaptureDTO:
        """Epic 006: an expense question, replacing ``replacing_id`` if set,
        in one transaction."""
        ...

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
        resulting_event_id: UUID | None = None,
        affected_count: int | None = None,
        resulting_expense_id: UUID | None = None,
    ) -> None: ...

    async def delete_turns_for_memories(
        self, *, user_id: UUID, memory_ids: list[UUID]
    ) -> int:
        """FR-23: delete every turn of these memories' threads."""
        ...

    async def list_turns_for_user(
        self, *, user_id: UUID, cursor: str | None, limit: int
    ) -> CaptureHistoryPageDTO: ...
