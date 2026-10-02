"""An in-memory PendingCaptureRepository."""

import uuid
from datetime import UTC, datetime

from app.domains.capture.interfaces.dtos import (
    ExpenseDraft,
    ExpenseQuestionKind,
    MissingField,
    PendingCaptureDTO,
)
from app.domains.memories.public import MemoryCategory


class FakePendingCaptureRepository:
    def __init__(self) -> None:
        self.rows: dict[uuid.UUID, PendingCaptureDTO] = {}

    async def create_pending_capture(
        self,
        *,
        user_id: uuid.UUID,
        command_name: str,
        known_title: str | None,
        missing_field: MissingField,
        question_text: str,
        original_input: str,
    ) -> PendingCaptureDTO:
        pending_capture = PendingCaptureDTO(
            id=uuid.uuid4(),
            user_id=user_id,
            command_name=command_name,
            known_title=known_title,
            missing_field=missing_field,
            question_text=question_text,
            original_input=original_input,
            asked_at=datetime.now(UTC),
        )
        self.rows[pending_capture.id] = pending_capture
        return pending_capture

    async def create_pending_conflict(
        self,
        *,
        user_id: uuid.UUID,
        command_name: str,
        question_text: str,
        original_input: str,
        candidate_text: str,
        candidate_category: MemoryCategory | None,
        conflicting_memory_ids: list[uuid.UUID],
    ) -> PendingCaptureDTO:
        pending_capture = PendingCaptureDTO(
            id=uuid.uuid4(),
            user_id=user_id,
            command_name=command_name,
            known_title=None,
            missing_field="memory_conflict",
            question_text=question_text,
            original_input=original_input,
            asked_at=datetime.now(UTC),
            candidate_text=candidate_text,
            candidate_category=candidate_category,
            conflicting_memory_ids=tuple(conflicting_memory_ids),
        )
        self.rows[pending_capture.id] = pending_capture
        return pending_capture

    async def create_pending_expense(
        self,
        *,
        user_id: uuid.UUID,
        kind: ExpenseQuestionKind,
        question_text: str,
        original_input: str,
        draft: ExpenseDraft,
        date_words: str | None,
        replacing_id: uuid.UUID | None,
    ) -> PendingCaptureDTO:
        if replacing_id is not None:
            await self.delete_pending_capture(
                user_id=user_id, pending_capture_id=replacing_id
            )
        pending_capture = PendingCaptureDTO(
            id=uuid.uuid4(),
            user_id=user_id,
            command_name="/add-expense",
            known_title=date_words,
            missing_field=kind.value,
            question_text=question_text,
            original_input=original_input,
            asked_at=datetime.now(UTC),
            expense_draft=draft,
        )
        self.rows[pending_capture.id] = pending_capture
        return pending_capture

    async def get_pending_capture(
        self, *, user_id: uuid.UUID, pending_capture_id: uuid.UUID
    ) -> PendingCaptureDTO | None:
        pending_capture = self.rows.get(pending_capture_id)
        if pending_capture is None or pending_capture.user_id != user_id:
            return None
        return pending_capture

    async def delete_pending_capture(
        self, *, user_id: uuid.UUID, pending_capture_id: uuid.UUID
    ) -> None:
        pending_capture = self.rows.get(pending_capture_id)
        if pending_capture is not None and pending_capture.user_id == user_id:
            del self.rows[pending_capture_id]
