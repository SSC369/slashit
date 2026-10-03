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
    ADD_EVENT_COMMAND,
    ADD_EXPENSE_COMMAND,
    CONFLICT_QUESTION,
    EVENTS_COMMAND,
    EXPENSES_COMMAND,
    FACT_QUESTION,
    KNOWN_COMMANDS,
    MAX_INPUT_LENGTH,
    MAX_MEMORY_LINE_LENGTH,
    MEMORY_SAVE_COMMANDS,
    SEARCH_COMMAND,
    SEARCH_QUESTION,
    TASK_EXTRACTION_INSTRUCTION,
    TASK_EXTRACTION_SCHEMA,
)
from app.domains.capture.interfaces.dtos import (
    CaptureTurnOutcome,
    EventListDTO,
    ExpenseQuestionAskedDTO,
    ExpenseRefusedDTO,
    MemoryConflictAskedDTO,
    MissingField,
    NonCommandGuidanceDTO,
    PendingCaptureDTO,
    ReminderListDTO,
    UnrecognisedCommandDTO,
)
from app.domains.capture.interfaces.ports import (
    AnalyticsPort,
    EventPort,
    ExtractionPort,
    MemoryPort,
    ReminderPort,
    SearchPort,
    TaskPort,
)
from app.domains.capture.interfaces.repositories import (
    CaptureTurnRepository,
    PendingCaptureRepository,
)
from app.domains.capture.services.event_capture import (
    EventCaptureService,
    EventNeedsTitle,
)
from app.domains.capture.services.expense_capture import (
    ExpenseAsk,
    ExpenseCaptureService,
    expense_question_asked,
)
from app.domains.capture.services.reminder_capture import (
    ReminderCaptureService,
    ReminderNeedsDescription,
)
from app.domains.events.public import (
    EventDTO,
    EventLimitReached,
    EventNeedsDate,
)
from app.domains.expenses.public import ExpenseDTO, ExpenseSummaryDTO
from app.domains.gateway.public import (
    Extraction,
    ExtractionResult,
    MalformedResult,
    ProviderTimeout,
    ProviderUnavailable,
    SharedQuotaExhausted,
    UserLimitReached,
)
from app.domains.memories.public import (
    MemoryConflictDTO,
    MemoryListDTO,
    MemorySavedDTO,
    MemoryTooLongDTO,
)
from app.domains.records.public import TaskDTO
from app.domains.reminders.public import (
    ReminderDTO,
    ReminderLimitReached,
    ReminderNeedsWhen,
)
from app.domains.search.public import (
    MAX_SEARCH_LENGTH,
    SearchResultsDTO,
    SearchTooLongDTO,
)

logger = structlog.get_logger(__name__)

CaptureOutcome = (
    TaskDTO
    | list[TaskDTO]
    | ReminderDTO
    | ReminderListDTO
    | ReminderLimitReached
    | EventDTO
    | EventListDTO
    | EventLimitReached
    | MemorySavedDTO
    | MemoryListDTO
    | MemoryTooLongDTO
    | MemoryConflictAskedDTO
    | SearchResultsDTO
    | SearchTooLongDTO
    | ExpenseDTO
    | ExpenseQuestionAskedDTO
    | ExpenseRefusedDTO
    | ExpenseSummaryDTO
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
        reminder_port: ReminderPort,
        reminder_capture: ReminderCaptureService,
        memory_port: MemoryPort,
        search_port: SearchPort,
        event_port: EventPort,
        event_capture: EventCaptureService,
        expense_capture: ExpenseCaptureService,
    ) -> None:
        self.pending_capture_repository = pending_capture_repository
        self.capture_turn_repository = capture_turn_repository
        self.task_port = task_port
        self.extraction = extraction
        self.analytics = analytics
        self.reminder_port = reminder_port
        self.reminder_capture = reminder_capture
        self.memory_port = memory_port
        self.search_port = search_port
        self.event_port = event_port
        self.event_capture = event_capture
        self.expense_capture = expense_capture

    async def submit_capture(self, *, user_id: UUID, raw_input: str) -> CaptureOutcome:
        """Run one capture on behalf of one user.

        Raises:
            ValueError: the input is empty or over its cap: 500 characters,
                or, for a memory save or a search, the outer guard of 1,000
                (AD-7, epic 005 FR-3). Not a
                ``CaptureOutcome`` member: a client bug, not an outcome.
        """
        text = self._validate_and_normalise(raw_input=raw_input)
        self._validate_line_length(text=text)

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

        if command_name == "/reminders":
            return ReminderListDTO(
                reminders=await self.reminder_port.list_active(user_id=user_id)
            )

        if command_name == "/remind":
            return await self._submit_remind(
                user_id=user_id, argument_text=argument_text, original_input=text
            )

        if command_name == EVENTS_COMMAND:
            return await self._list_events(user_id=user_id, original_input=text)

        if command_name == ADD_EVENT_COMMAND:
            return await self._submit_add_event(
                user_id=user_id, argument_text=argument_text, original_input=text
            )

        if command_name == ADD_EXPENSE_COMMAND:
            return await self._submit_expense(
                user_id=user_id, argument_text=argument_text, original_input=text
            )

        if command_name == EXPENSES_COMMAND:
            return await self._summarise_expenses(
                user_id=user_id, argument_text=argument_text, original_input=text
            )

        if command_name == SEARCH_COMMAND:
            return await self._submit_search(
                user_id=user_id, argument_text=argument_text, original_input=text
            )

        if command_name == "/memories":
            return await self._list_memories(
                user_id=user_id, argument_text=argument_text, original_input=text
            )

        if command_name in MEMORY_SAVE_COMMANDS:
            return await self._submit_memory(
                user_id=user_id,
                command_name=command_name,
                argument_text=argument_text,
                original_input=text,
            )

        return await self._submit_add_task(
            user_id=user_id, argument_text=argument_text, original_input=text
        )

    def _validate_and_normalise(self, *, raw_input: str) -> str:
        text = raw_input.strip()
        if not text:
            raise ValueError("capture input is empty")
        if len(text) > MAX_MEMORY_LINE_LENGTH:
            raise ValueError(
                f"capture input exceeds {MAX_MEMORY_LINE_LENGTH} characters"
            )
        return text

    def _validate_line_length(self, *, text: str) -> None:
        """AD-7: a memory save's fact is measured by memories, which answers
        an over-long fact with a drawn state (FR-4). An expense line is the
        same: FR-13 judges its description (006 dev log E-3). Every other
        line keeps 001's 500-character cap."""
        command_name, _ = self._split_command(text=text)
        if command_name in (*MEMORY_SAVE_COMMANDS, SEARCH_COMMAND, ADD_EXPENSE_COMMAND):
            return
        if len(text) > MAX_INPUT_LENGTH:
            raise ValueError(f"capture input exceeds {MAX_INPUT_LENGTH} characters")

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

    async def _submit_remind(
        self, *, user_id: UUID, argument_text: str, original_input: str
    ) -> CaptureOutcome:
        """Epic 003, FR-1, FR-2, FR-38. Reading and creating is the shared
        ReminderCaptureService's; turning its outcome into a question, a turn
        and a result is this interactor's."""
        outcome = await self.reminder_capture.capture_reminder(
            user_id=user_id, argument_text=argument_text, original_input=original_input
        )
        if isinstance(outcome, ReminderNeedsDescription):
            return await self._ask_pending_question(
                user_id=user_id,
                command_name="/remind",
                known_title=None,
                missing_field="title",
                question_text="What should I remind you about?",
                original_input=original_input,
            )
        if isinstance(outcome, ReminderNeedsWhen):
            return await self._ask_pending_question(
                user_id=user_id,
                command_name="/remind",
                known_title=outcome.description,
                missing_field="remind_at",
                question_text=when_question(description=outcome.description),
                original_input=original_input,
            )
        if isinstance(outcome, ReminderDTO):
            await self._record_turn(
                user_id=user_id,
                input_text=original_input,
                outcome="reminder_created",
                resulting_reminder_id=outcome.id,
            )
            return outcome
        await self._record_turn(
            user_id=user_id, input_text=original_input, outcome="refused"
        )
        return outcome

    async def _submit_add_event(
        self, *, user_id: UUID, argument_text: str, original_input: str
    ) -> CaptureOutcome:
        """Epic 007, FR-1, FR-2, FR-31. Reading and creating is the
        shared EventCaptureService's; turning its outcome into a question, a
        turn and a result is this interactor's."""
        outcome = await self.event_capture.capture_event(
            user_id=user_id, argument_text=argument_text, original_input=original_input
        )
        if isinstance(outcome, EventNeedsTitle):
            return await self._ask_pending_question(
                user_id=user_id,
                command_name=ADD_EVENT_COMMAND,
                known_title=None,
                missing_field="title",
                question_text="What is the event?",
                original_input=original_input,
            )
        if isinstance(outcome, EventNeedsDate):
            return await self._ask_pending_question(
                user_id=user_id,
                command_name=ADD_EVENT_COMMAND,
                known_title=argument_text,
                missing_field="event_date",
                question_text=event_date_question(title=outcome.title),
                original_input=original_input,
            )
        if isinstance(outcome, EventDTO):
            await self._record_turn(
                user_id=user_id,
                input_text=original_input,
                outcome="event_created",
                resulting_event_id=outcome.id,
            )
            return outcome
        await self._record_turn(
            user_id=user_id, input_text=original_input, outcome="refused"
        )
        return outcome

    async def _list_events(self, *, user_id: UUID, original_input: str) -> EventListDTO:
        """Epic 007, FR-24: upcoming events, soonest first."""
        events = await self.event_port.list_upcoming(user_id=user_id)
        await self._record_turn(
            user_id=user_id, input_text=original_input, outcome="events_listed"
        )
        return EventListDTO(events=events)

    async def _submit_expense(
        self, *, user_id: UUID, argument_text: str, original_input: str
    ) -> CaptureOutcome:
        """Epic 006, FR-1 to FR-15. Reading and deciding is the shared
        ExpenseCaptureService's; storing a question and a turn is this
        interactor's."""
        outcome = await self.expense_capture.capture(
            user_id=user_id, argument_text=argument_text, original_input=original_input
        )
        if isinstance(outcome, ExpenseAsk):
            return await self._ask_expense_question(
                user_id=user_id, ask=outcome, original_input=original_input
            )
        if isinstance(outcome, ExpenseDTO):
            await self._record_turn(
                user_id=user_id,
                input_text=original_input,
                outcome="expense_saved",
                resulting_expense_id=outcome.id,
            )
            return outcome
        # A refusal, or one of the gateway's failure members (FR-14).
        await self._record_turn(
            user_id=user_id, input_text=original_input, outcome="refused"
        )
        return outcome

    async def _summarise_expenses(
        self, *, user_id: UUID, argument_text: str, original_input: str
    ) -> ExpenseSummaryDTO | ExpenseRefusedDTO:
        """Epic 006, FR-23 to FR-27. The turn keeps the line, never the
        totals: history reruns it, as a search's does."""
        outcome = await self.expense_capture.summarise(
            user_id=user_id, argument_text=argument_text
        )
        await self._record_turn(
            user_id=user_id,
            input_text=original_input,
            outcome=(
                "expenses_summarised"
                if isinstance(outcome, ExpenseSummaryDTO)
                else "refused"
            ),
        )
        return outcome

    async def _ask_expense_question(
        self, *, user_id: UUID, ask: ExpenseAsk, original_input: str
    ) -> ExpenseQuestionAskedDTO:
        pending = await self.pending_capture_repository.create_pending_expense(
            user_id=user_id,
            kind=ask.kind,
            question_text=ask.question,
            original_input=original_input,
            draft=ask.draft,
            date_words=ask.date_words,
            replacing_id=None,
        )
        await self._record_turn(
            user_id=user_id,
            input_text=original_input,
            outcome="question_asked",
            resulting_pending_capture_id=pending.id,
            question_text=ask.question,
        )
        return expense_question_asked(pending_capture_id=pending.id, ask=ask)

    async def _submit_memory(
        self,
        *,
        user_id: UUID,
        command_name: str,
        argument_text: str,
        original_input: str,
    ) -> CaptureOutcome:
        """Epic 004, FR-1 to FR-9. An empty fact asks one question (FR-3);
        anything else goes to memories, which owns every rule about facts."""
        if not argument_text:
            return await self._ask_pending_question(
                user_id=user_id,
                command_name=command_name,
                known_title=None,
                missing_field="fact",
                question_text=FACT_QUESTION,
                original_input=original_input,
            )
        outcome = await self.memory_port.save_memory(
            user_id=user_id, text=argument_text, original_input=original_input
        )
        if isinstance(outcome, MemorySavedDTO):
            await self._record_turn(
                user_id=user_id,
                input_text=original_input,
                outcome="memory_saved",
                resulting_memory_id=outcome.memory.id,
            )
            return outcome
        if isinstance(outcome, MemoryConflictDTO):
            return await self._ask_conflict(
                user_id=user_id,
                command_name=command_name,
                conflict=outcome,
                original_input=original_input,
            )
        await self._record_turn(
            user_id=user_id, input_text=original_input, outcome="refused"
        )
        return outcome

    async def _submit_search(
        self, *, user_id: UUID, argument_text: str, original_input: str
    ) -> PendingCaptureDTO | SearchResultsDTO | SearchTooLongDTO:
        """Epic 005, FR-1 to FR-3. An empty search asks one question; an
        over-long one is refused with its length; anything else is searched.
        The turn keeps the typed line only, never the results (FR-21)."""
        if not argument_text:
            return await self._ask_pending_question(
                user_id=user_id,
                command_name=SEARCH_COMMAND,
                known_title=None,
                missing_field="search_text",
                question_text=SEARCH_QUESTION,
                original_input=original_input,
            )
        if len(argument_text) > MAX_SEARCH_LENGTH:
            await self._record_turn(
                user_id=user_id, input_text=original_input, outcome="refused"
            )
            return SearchTooLongDTO(length=len(argument_text))
        results = await self.search_port.search(user_id=user_id, text=argument_text)
        await self._record_turn(
            user_id=user_id, input_text=original_input, outcome="searched"
        )
        return results

    async def _list_memories(
        self, *, user_id: UUID, argument_text: str, original_input: str
    ) -> MemoryListDTO:
        """Epic 004, FR-19 and FR-20: every memory, or those matching words."""
        if argument_text:
            memory_list = await self.memory_port.look_up_memories(
                user_id=user_id, text=argument_text
            )
        else:
            memory_list = await self.memory_port.list_memories(user_id=user_id)
        await self._record_turn(
            user_id=user_id, input_text=original_input, outcome="memory_listed"
        )
        return memory_list

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

    async def _ask_conflict(
        self,
        *,
        user_id: UUID,
        command_name: str,
        conflict: MemoryConflictDTO,
        original_input: str,
    ) -> MemoryConflictAskedDTO:
        """FR-10 and FR-13: nothing is saved; the fact waits for an answer."""
        pending = await self.pending_capture_repository.create_pending_conflict(
            user_id=user_id,
            command_name=command_name,
            question_text=CONFLICT_QUESTION,
            original_input=original_input,
            candidate_text=conflict.text,
            candidate_category=conflict.category,
            conflicting_memory_ids=[memory.id for memory in conflict.conflicting],
        )
        await self._record_turn(
            user_id=user_id,
            input_text=original_input,
            outcome="question_asked",
            resulting_pending_capture_id=pending.id,
            question_text=CONFLICT_QUESTION,
        )
        return MemoryConflictAskedDTO(
            pending_capture_id=pending.id,
            question=CONFLICT_QUESTION,
            text=conflict.text,
            category=conflict.category,
            conflicting=conflict.conflicting,
        )

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
        resulting_reminder_id: UUID | None = None,
        resulting_memory_id: UUID | None = None,
        resulting_event_id: UUID | None = None,
        resulting_expense_id: UUID | None = None,
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
                resulting_reminder_id=resulting_reminder_id,
                resulting_memory_id=resulting_memory_id,
                resulting_event_id=resulting_event_id,
                resulting_expense_id=resulting_expense_id,
            )
        except Exception:
            logger.exception(
                "capture_turn.record_failed", user_id=str(user_id), outcome=outcome
            )


def when_question(*, description: str) -> str:
    """FR-2's one question, as the design's `RemindAsk` draws it, with the
    description lowercased to sit mid-sentence."""
    phrase = description[:1].lower() + description[1:]
    return f"When should I remind you to {phrase}?"


def event_date_question(*, title: str) -> str:
    """FR-2's one question for an event, as the design's `EventAsk` draws it."""
    return f"When is \u201c{title}\u201d?"
