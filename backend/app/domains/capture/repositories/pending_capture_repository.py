"""The only SQL in the capture domain. Returns DTOs, never models."""

import uuid
from datetime import UTC, datetime
from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import user_transaction
from app.domains.capture.interfaces.dtos import MissingField, PendingCaptureDTO
from app.domains.capture.models import PendingCapture
from app.domains.memories.public import MemoryCategory


class SqlPendingCaptureRepository:
    """Against the request's own session. See task_repository.py's docstring
    for why this differs from the gateway's own session-factory pattern."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

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
        now = datetime.now(UTC)
        pending_capture_id = uuid.uuid4()
        async with user_transaction(self.session, user_id) as scoped:
            scoped.add(
                PendingCapture(
                    id=pending_capture_id,
                    user_id=user_id,
                    command_name=command_name,
                    known_title=known_title,
                    missing_field=missing_field,
                    question_text=question_text,
                    original_input=original_input,
                    asked_at=now,
                )
            )
        return PendingCaptureDTO(
            id=pending_capture_id,
            user_id=user_id,
            command_name=command_name,
            known_title=known_title,
            missing_field=missing_field,
            question_text=question_text,
            original_input=original_input,
            asked_at=now,
        )

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
        """Epic 004, FR-10 and FR-13: the new fact waits here, unsaved."""
        pending_capture = PendingCapture(
            id=uuid.uuid4(),
            user_id=user_id,
            command_name=command_name,
            known_title=None,
            missing_field="memory_conflict",
            question_text=question_text,
            original_input=original_input,
            asked_at=datetime.now(UTC),
            candidate_text=candidate_text,
            candidate_category=candidate_category.value if candidate_category else None,
            conflicting_memory_ids=list(conflicting_memory_ids),
        )
        async with user_transaction(self.session, user_id) as scoped:
            scoped.add(pending_capture)
        return _pending_capture_to_dto(pending_capture=pending_capture)

    async def get_pending_capture(
        self, *, user_id: uuid.UUID, pending_capture_id: uuid.UUID
    ) -> PendingCaptureDTO | None:
        async with user_transaction(self.session, user_id) as scoped:
            pending_capture = await scoped.get(PendingCapture, pending_capture_id)
            if pending_capture is None or pending_capture.user_id != user_id:
                return None
            return _pending_capture_to_dto(pending_capture=pending_capture)

    async def delete_pending_capture(
        self, *, user_id: uuid.UUID, pending_capture_id: uuid.UUID
    ) -> None:
        async with user_transaction(self.session, user_id) as scoped:
            pending_capture = await scoped.get(PendingCapture, pending_capture_id)
            if pending_capture is not None:
                await scoped.delete(pending_capture)


def _pending_capture_to_dto(*, pending_capture: PendingCapture) -> PendingCaptureDTO:
    return PendingCaptureDTO(
        id=pending_capture.id,
        user_id=pending_capture.user_id,
        command_name=pending_capture.command_name,
        known_title=pending_capture.known_title,
        missing_field=cast(MissingField, pending_capture.missing_field),
        question_text=pending_capture.question_text,
        original_input=pending_capture.original_input,
        asked_at=pending_capture.asked_at,
        candidate_text=pending_capture.candidate_text,
        candidate_category=(
            MemoryCategory(pending_capture.candidate_category)
            if pending_capture.candidate_category
            else None
        ),
        conflicting_memory_ids=tuple(pending_capture.conflicting_memory_ids or ()),
    )
