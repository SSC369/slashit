"""Answer a pending capture, whenever the user gets to it. FR-37, FR-38."""

from datetime import datetime
from typing import Any, cast
from uuid import UUID

import structlog

from app.domains.capture.constants import DUE_AT_ONLY_INSTRUCTION, DUE_AT_ONLY_SCHEMA
from app.domains.capture.interfaces.ports import ExtractionPort, TaskPort
from app.domains.capture.interfaces.repositories import (
    CaptureTurnRepository,
    PendingCaptureRepository,
)
from app.domains.capture.services.reminder_capture import (
    ReminderCaptureOutcome,
    ReminderCaptureService,
    ReminderNeedsDescription,
)
from app.domains.gateway.public import Extraction
from app.domains.records.public import TaskDTO
from app.domains.reminders.public import ReminderDTO, ReminderNeedsWhen

AnswerOutcome = TaskDTO | ReminderCaptureOutcome

logger = structlog.get_logger(__name__)


class PendingCaptureNotFoundError(Exception):
    """Raised when the pending capture does not exist, or belongs to another
    user. Not a DomainError: there is no screen for this, since the frontend
    never holds an id it did not receive from its own account. Mapped to a
    plain GraphQL error by the resolver, not a union member.
    """


class AnswerCouldNotBeUnderstoodError(Exception):
    """The answer did not resolve to what the question asked for."""


class AnswerPendingCaptureInteractor:
    def __init__(
        self,
        *,
        pending_capture_repository: PendingCaptureRepository,
        capture_turn_repository: CaptureTurnRepository,
        task_port: TaskPort,
        extraction: ExtractionPort,
        reminder_capture: ReminderCaptureService,
    ) -> None:
        self.pending_capture_repository = pending_capture_repository
        self.capture_turn_repository = capture_turn_repository
        self.task_port = task_port
        self.extraction = extraction
        self.reminder_capture = reminder_capture

    async def answer_pending_capture(
        self, *, user_id: UUID, pending_capture_id: UUID, answer: str
    ) -> AnswerOutcome:
        """Resolve a pending capture with the user's answer, creating the task,
        or, for a `/remind` question (epic 003, FR-2), the reminder.

        Raises:
            PendingCaptureNotFoundError: no such pending capture for this user.
            ValueError: the answer is empty.
            AnswerCouldNotBeUnderstoodError: a due-date answer that the model
                could not resolve to a date, per FR-38's own reference moment.
        """
        pending_capture = await self.pending_capture_repository.get_pending_capture(
            user_id=user_id, pending_capture_id=pending_capture_id
        )
        if pending_capture is None:
            raise PendingCaptureNotFoundError()

        answer_text = answer.strip()
        if not answer_text:
            raise ValueError("answer is empty")

        if pending_capture.command_name == "/remind":
            return await self._answer_remind(
                user_id=user_id,
                pending_capture_id=pending_capture_id,
                known_description=pending_capture.known_title,
                question_text=pending_capture.question_text,
                original_input=pending_capture.original_input,
                answer_text=answer_text,
            )

        if pending_capture.missing_field == "title":
            title = answer_text
            due_at = None
        else:
            title = pending_capture.known_title or answer_text
            due_at = await self._resolve_due_at(
                user_id=user_id, answer_text=answer_text
            )
            if due_at is None:
                raise AnswerCouldNotBeUnderstoodError()

        task = await self.task_port.create_task(
            user_id=user_id,
            title=title,
            due_at=due_at,
            # FR-38: the answer resolves against the moment the original
            # capture was made, not the moment it was answered.
            original_input=pending_capture.original_input,
        )
        await self._record_turn(
            user_id=user_id,
            input_text=pending_capture.original_input,
            resulting_task_id=task.id,
            pending_capture_id=pending_capture_id,
            question_text=pending_capture.question_text,
            answer_text=answer_text,
        )
        await self.pending_capture_repository.delete_pending_capture(
            user_id=user_id, pending_capture_id=pending_capture_id
        )
        return task

    async def _answer_remind(
        self,
        *,
        user_id: UUID,
        pending_capture_id: UUID,
        known_description: str | None,
        question_text: str,
        original_input: str,
        answer_text: str,
    ) -> ReminderCaptureOutcome:
        """The answer completes the sentence: the description asked for, or
        the known description plus when. It is read exactly as a whole
        sentence would be. An answer that still sets no time raises, and the
        question stays open, as a due-date answer does."""
        argument_text = (
            f"{known_description} {answer_text}" if known_description else answer_text
        )
        outcome = await self.reminder_capture.capture_reminder(
            user_id=user_id, argument_text=argument_text, original_input=original_input
        )
        if isinstance(outcome, ReminderNeedsWhen | ReminderNeedsDescription):
            raise AnswerCouldNotBeUnderstoodError()
        if not isinstance(outcome, ReminderDTO):
            return outcome
        try:
            await self.capture_turn_repository.record_turn(
                user_id=user_id,
                input_text=original_input,
                outcome="reminder_created",
                resulting_task_id=None,
                resulting_pending_capture_id=pending_capture_id,
                question_text=question_text,
                answer_text=answer_text,
                resulting_reminder_id=outcome.id,
            )
        except Exception:
            # Same rule as _record_turn: the log never undoes the reminder.
            logger.exception("capture_turn.record_failed", user_id=str(user_id))
        await self.pending_capture_repository.delete_pending_capture(
            user_id=user_id, pending_capture_id=pending_capture_id
        )
        return outcome

    async def _record_turn(
        self,
        *,
        user_id: UUID,
        input_text: str,
        resulting_task_id: UUID,
        pending_capture_id: UUID,
        question_text: str,
        answer_text: str,
    ) -> None:
        """FR-44. A capture-turn write failure never undoes the task already
        created: NFR-9's "no capture is lost" binds the task, not the log of
        it, per the 04.4 sub-plan section 9."""
        try:
            await self.capture_turn_repository.record_turn(
                user_id=user_id,
                input_text=input_text,
                outcome="task_created",
                resulting_task_id=resulting_task_id,
                resulting_pending_capture_id=pending_capture_id,
                question_text=question_text,
                answer_text=answer_text,
            )
        except Exception:
            logger.exception("capture_turn.record_failed", user_id=str(user_id))

    async def _resolve_due_at(
        self, *, user_id: UUID, answer_text: str
    ) -> datetime | None:
        """Resolve a free-text due-date answer ("Friday", "tomorrow") through
        the same gateway extraction path capture itself uses, rather than a
        second date-parsing dependency this domain would otherwise need.
        """
        result = await self.extraction.extract(
            user_id=user_id,
            prompt=answer_text,
            schema=DUE_AT_ONLY_SCHEMA,
            instruction=DUE_AT_ONLY_INSTRUCTION,
        )
        if not isinstance(result, Extraction):
            return None
        raw_due_at = cast(dict[str, Any], result.data).get("due_at")
        if not isinstance(raw_due_at, str) or not raw_due_at:
            return None
        try:
            return datetime.fromisoformat(raw_due_at)
        except ValueError:
            return None
