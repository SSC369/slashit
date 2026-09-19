"""Capture's one use case: turn one line of text into a task, a question, an
honest refusal, or guidance.

Returns a DTO or, for a gateway failure, the gateway's own union member
unmapped. It never returns a GraphQL type: that conversion is the resolver's
job (graphql/mutations.py), per repo-rules.md section 7 — an interactor
imports nothing from graphql/. No ``@map_errors``: every outcome here is a
plain return, mirroring the gateway's own ``ExtractInteractor``. The one
exception is validation, which raises before any I/O, because an empty or
oversized mutation input is a client bug, not an outcome the design draws a
screen for.
"""

import difflib
from datetime import datetime
from typing import Any, cast
from uuid import UUID

import structlog

from app.domains.capture.constants import (
    KNOWN_COMMANDS,
    MAX_INPUT_LENGTH,
    TASK_EXTRACTION_INSTRUCTION,
    TASK_EXTRACTION_SCHEMA,
)
from app.domains.capture.interfaces.dtos import (
    CaptureTurnOutcome,
    MissingField,
    NonCommandGuidanceDTO,
    PendingCaptureDTO,
    UnrecognisedCommandDTO,
)
from app.domains.capture.interfaces.ports import AnalyticsPort, ExtractionPort, TaskPort
from app.domains.capture.interfaces.repositories import (
    CaptureTurnRepository,
    PendingCaptureRepository,
)
from app.domains.gateway.public import (
    Extraction,
    ExtractionResult,
    MalformedResult,
    ProviderTimeout,
    ProviderUnavailable,
    SharedQuotaExhausted,
    UserLimitReached,
)
from app.domains.records.public import TaskDTO

logger = structlog.get_logger(__name__)

CaptureOutcome = (
    TaskDTO
    | list[TaskDTO]
    | PendingCaptureDTO
    | NonCommandGuidanceDTO
    | UnrecognisedCommandDTO
    | UserLimitReached
    | ProviderUnavailable
    | ProviderTimeout
    | SharedQuotaExhausted
    | MalformedResult
)


class SubmitCaptureInteractor:
    def __init__(
        self,
        *,
        pending_capture_repository: PendingCaptureRepository,
        capture_turn_repository: CaptureTurnRepository,
        task_port: TaskPort,
        extraction: ExtractionPort,
        analytics: AnalyticsPort,
    ) -> None:
        self.pending_capture_repository = pending_capture_repository
        self.capture_turn_repository = capture_turn_repository
        self.task_port = task_port
        self.extraction = extraction
        self.analytics = analytics

    async def submit_capture(self, *, user_id: UUID, raw_input: str) -> CaptureOutcome:
        """Run one capture on behalf of one user.

        Raises:
            ValueError: the input is empty or over the 500-character cap.
                Not a ``CaptureOutcome`` member: a client bug, not an outcome.
        """
        text = self._validate_and_normalise(raw_input=raw_input)

        if not text.startswith("/"):
            await self._record_no_command_input(user_id=user_id)
            return NonCommandGuidanceDTO(original_input=text)

        command_name, argument_text = self._split_command(text=text)

        if command_name not in KNOWN_COMMANDS:
            return UnrecognisedCommandDTO(
                attempted_name=command_name,
                closest_matches=difflib.get_close_matches(
                    command_name, KNOWN_COMMANDS, n=3
                ),
            )

        if command_name == "/tasks":
            return await self.task_port.list_open_tasks(user_id=user_id)

        return await self._submit_add_task(
            user_id=user_id, argument_text=argument_text, original_input=text
        )

    def _validate_and_normalise(self, *, raw_input: str) -> str:
        text = raw_input.strip()
        if not text:
            raise ValueError("capture input is empty")
        if len(text) > MAX_INPUT_LENGTH:
            raise ValueError(f"capture input exceeds {MAX_INPUT_LENGTH} characters")
        return text

    def _split_command(self, *, text: str) -> tuple[str, str]:
        command_name, _, argument_text = text.partition(" ")
        return command_name, argument_text.strip()

    async def _submit_add_task(
        self, *, user_id: UUID, argument_text: str, original_input: str
    ) -> CaptureOutcome:
        if not argument_text:
            return await self._ask_pending_question(
                user_id=user_id,
                command_name="/add-task",
                known_title=None,
                missing_field="title",
                question_text="What should the task be called?",
                original_input=original_input,
            )

        extraction_result: ExtractionResult = await self.extraction.extract(
            user_id=user_id,
            prompt=argument_text,
            schema=TASK_EXTRACTION_SCHEMA,
            instruction=TASK_EXTRACTION_INSTRUCTION,
        )
        if not isinstance(extraction_result, Extraction):
            # One of the gateway's five failure members. Returned unmapped,
            # straight through, per build plan section 7.
            await self._record_turn(
                user_id=user_id, input_text=original_input, outcome="refused"
            )
            return extraction_result

        extracted_fields = cast(dict[str, Any], extraction_result.data)
        title = extracted_fields.get("title")
        if not title:
            return await self._ask_pending_question(
                user_id=user_id,
                command_name="/add-task",
                known_title=None,
                missing_field="title",
                question_text="What should the task be called?",
                original_input=original_input,
            )

        due_at = self._parse_due_at(raw_due_at=extracted_fields.get("due_at"))
        if due_at is None:
            # Covers both an omitted due_at and one the model returned that
            # does not parse as ISO 8601. The latter is rare and non-
            # actionable enough that it is not worth a distinct outcome.
            return await self._ask_pending_question(
                user_id=user_id,
                command_name="/add-task",
                known_title=str(title),
                missing_field="due_at",
                question_text=f'When is "{title}" due?',
                original_input=original_input,
            )

        task = await self.task_port.create_task(
            user_id=user_id,
            title=str(title),
            due_at=due_at,
            original_input=original_input,
        )
        await self._record_turn(
            user_id=user_id,
            input_text=original_input,
            outcome="task_created",
            resulting_task_id=task.id,
        )
        return task

    def _parse_due_at(self, *, raw_due_at: object) -> datetime | None:
        if not isinstance(raw_due_at, str) or not raw_due_at:
            return None
        try:
            return datetime.fromisoformat(raw_due_at)
        except ValueError:
            return None

    async def _ask_pending_question(
        self,
        *,
        user_id: UUID,
        command_name: str,
        known_title: str | None,
        missing_field: MissingField,
        question_text: str,
        original_input: str,
    ) -> PendingCaptureDTO:
        pending_capture = await self.pending_capture_repository.create_pending_capture(
            user_id=user_id,
            command_name=command_name,
            known_title=known_title,
            missing_field=missing_field,
            question_text=question_text,
            original_input=original_input,
        )
        await self._record_turn(
            user_id=user_id,
            input_text=original_input,
            outcome="question_asked",
            resulting_pending_capture_id=pending_capture.id,
            question_text=question_text,
        )
        return pending_capture

    async def _record_no_command_input(self, *, user_id: UUID) -> None:
        """FR-9's metric (PRD section 8). Same non-blocking pattern as
        _record_turn: an instrumentation write failure never turns a
        successful guidance response into an error."""
        try:
            await self.analytics.record_no_command_input(user_id=user_id)
        except Exception:
            logger.exception("analytics.no_command_input_failed", user_id=str(user_id))

    async def _record_turn(
        self,
        *,
        user_id: UUID,
        input_text: str,
        outcome: CaptureTurnOutcome,
        resulting_task_id: UUID | None = None,
        resulting_pending_capture_id: UUID | None = None,
        question_text: str | None = None,
    ) -> None:
        """FR-44. A capture-turn write failure never undoes an otherwise
        successful capture: NFR-9's "no capture is lost" binds the task or
        question, not the log of it, per the 04.4 sub-plan section 9."""
        try:
            await self.capture_turn_repository.record_turn(
                user_id=user_id,
                input_text=input_text,
                outcome=outcome,
                resulting_task_id=resulting_task_id,
                resulting_pending_capture_id=resulting_pending_capture_id,
                question_text=question_text,
                answer_text=None,
            )
        except Exception:
            logger.exception(
                "capture_turn.record_failed", user_id=str(user_id), outcome=outcome
            )
