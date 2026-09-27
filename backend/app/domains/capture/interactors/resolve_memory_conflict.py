"""Answer "Which is correct?". Epic 004, FR-11 to FR-13.

Lives in capture because the waiting conflict is a pending capture and its
answer is a turn in capture history. Memories owns what each answer does to
the memories themselves.
"""

from uuid import UUID

import structlog

from app.domains.capture.constants import CONFLICT_ANSWER_LABELS, CONFLICT_QUESTION
from app.domains.capture.interfaces.dtos import PendingCaptureDTO, PendingCaptureGoneDTO
from app.domains.capture.interfaces.ports import MemoryPort
from app.domains.capture.interfaces.repositories import (
    CaptureTurnRepository,
    PendingCaptureRepository,
)
from app.domains.memories.public import (
    ConflictAnswer,
    MemoryDiscardedDTO,
    MemorySavedDTO,
)

logger = structlog.get_logger(__name__)

ResolveConflictOutcome = MemorySavedDTO | MemoryDiscardedDTO | PendingCaptureGoneDTO


class ResolveMemoryConflictInteractor:
    def __init__(
        self,
        *,
        pending_capture_repository: PendingCaptureRepository,
        capture_turn_repository: CaptureTurnRepository,
        memory_port: MemoryPort,
    ) -> None:
        self.pending_capture_repository = pending_capture_repository
        self.capture_turn_repository = capture_turn_repository
        self.memory_port = memory_port

    async def resolve_memory_conflict(
        self, *, user_id: UUID, pending_capture_id: UUID, answer: ConflictAnswer
    ) -> ResolveConflictOutcome:
        """Apply the user's answer, then close the question.

        A conflict already answered or discarded, or another user's, is
        ``PendingCaptureGoneDTO`` and changes nothing (FR-13, T7).
        """
        pending = await self._find_waiting_conflict(
            user_id=user_id, pending_capture_id=pending_capture_id
        )
        if pending is None:
            return PendingCaptureGoneDTO()

        outcome = await self.memory_port.resolve_conflict(
            user_id=user_id,
            text=pending.candidate_text or "",
            category=pending.candidate_category,
            original_input=pending.original_input,
            conflicting_ids=list(pending.conflicting_memory_ids),
            answer=answer,
        )
        await self._record_resolution_turn(
            user_id=user_id, pending=pending, answer=answer, outcome=outcome
        )
        await self.pending_capture_repository.delete_pending_capture(
            user_id=user_id, pending_capture_id=pending.id
        )
        return outcome

    async def _find_waiting_conflict(
        self, *, user_id: UUID, pending_capture_id: UUID
    ) -> PendingCaptureDTO | None:
        pending = await self.pending_capture_repository.get_pending_capture(
            user_id=user_id, pending_capture_id=pending_capture_id
        )
        if pending is None or pending.missing_field != "memory_conflict":
            return None
        return pending

    async def _record_resolution_turn(
        self,
        *,
        user_id: UUID,
        pending: PendingCaptureDTO,
        answer: ConflictAnswer,
        outcome: MemorySavedDTO | MemoryDiscardedDTO,
    ) -> None:
        """Carries the pending id and the new memory's id, so a later forget
        scrubs the whole thread (sub-plan 4.3 §5). Never raises: the log never
        undoes the answer, as with every capture turn."""
        try:
            await self.capture_turn_repository.record_turn(
                user_id=user_id,
                input_text=pending.original_input,
                outcome="memory_conflict_resolved",
                resulting_task_id=None,
                resulting_pending_capture_id=pending.id,
                question_text=CONFLICT_QUESTION,
                answer_text=CONFLICT_ANSWER_LABELS[answer.value],
                resulting_memory_id=(
                    outcome.memory.id if isinstance(outcome, MemorySavedDTO) else None
                ),
            )
        except Exception:
            # Broad on purpose: a history write failure is logged, never shown.
            logger.exception("capture_turn.record_failed", user_id=str(user_id))
