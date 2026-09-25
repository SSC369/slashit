"""Confirm a `/forget`: forget, then record the turn. Epic 004, FR-24 to FR-28.

Lives in capture, not memories, because the `/forget` turn belongs to capture
history, which capture owns. The turn stores ``input_text = '/forget'`` and the
count, never the words typed after the command: "forget my passport number"
would otherwise keep the fact it was meant to remove (FR-28).
"""

from uuid import UUID

import structlog

from app.domains.capture.interfaces.ports import MemoryPort
from app.domains.capture.interfaces.repositories import CaptureTurnRepository
from app.domains.memories.public import MemoriesForgottenDTO, MemoryCountChangedDTO

logger = structlog.get_logger(__name__)

FORGET_TURN_INPUT = "/forget"

ConfirmForgetOutcome = MemoriesForgottenDTO | MemoryCountChangedDTO


class ConfirmForgetInteractor:
    def __init__(
        self,
        *,
        memory_port: MemoryPort,
        capture_turn_repository: CaptureTurnRepository,
    ) -> None:
        self.memory_port = memory_port
        self.capture_turn_repository = capture_turn_repository

    async def confirm_forget(
        self,
        *,
        user_id: UUID,
        memory_ids: list[UUID],
        forget_all: bool,
        expected_count: int,
    ) -> ConfirmForgetOutcome:
        """Forget what the user confirmed. A zero count means none of the ids
        were the caller's live memories; the resolver answers it as gone."""
        if forget_all:
            outcome = await self.memory_port.forget_all(
                user_id=user_id, expected_count=expected_count
            )
        else:
            outcome = await self.memory_port.forget_memories(
                user_id=user_id, memory_ids=memory_ids
            )
        if isinstance(outcome, MemoriesForgottenDTO) and outcome.count > 0:
            await self._record_forget_turn(user_id=user_id, count=outcome.count)
        return outcome

    async def _record_forget_turn(self, *, user_id: UUID, count: int) -> None:
        """FR-44 and FR-28. A turn-write failure never undoes the forget."""
        try:
            await self.capture_turn_repository.record_turn(
                user_id=user_id,
                input_text=FORGET_TURN_INPUT,
                outcome="memory_forgotten",
                resulting_task_id=None,
                resulting_pending_capture_id=None,
                question_text=None,
                answer_text=None,
                affected_count=count,
            )
        except Exception:
            # Broad on purpose: the log never undoes what it logs.
            logger.exception("capture_turn.record_failed", user_id=str(user_id))
