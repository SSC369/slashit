"""Capture's mutations: submit, answer, discard.

The resolver's own job, per repo-rules.md section 7.2: read context, build the
interactor, call it, and convert whatever DTO it returned into the matching
GraphQL type. No business rule lives here.
"""

from typing import Annotated, cast
from uuid import UUID

import strawberry
from strawberry.types import Info

from app.core.context import Context
from app.core.deps import (
    build_answer_pending_capture_interactor,
    build_discard_pending_capture_interactor,
    build_resolve_memory_conflict_interactor,
    build_submit_capture_interactor,
)
from app.domains.capture.constants import EXPENSE_AMOUNT_TOO_LARGE
from app.domains.capture.graphql.types import (
    EventCreated,
    EventLimitReached,
    EventsListed,
    ExpenseQuestionAsked,
    ExpenseRefused,
    ExpenseSaved,
    MemoriesListed,
    MemoryConflictAsked,
    MemoryDiscarded,
    MemorySaved,
    NonCommandGuidance,
    PendingCaptureNotFound,
    PendingQuestionCreated,
    ReminderCreated,
    ReminderLimitReached,
    RemindersListed,
    TaskCreated,
    TasksListed,
    UnrecognisedCommand,
)
from app.domains.capture.interactors.answer_pending_capture import AnswerOutcome
from app.domains.capture.interactors.submit_capture import CaptureOutcome
from app.domains.capture.interfaces.dtos import (
    EventListDTO,
    ExpenseQuestionAskedDTO,
    ExpenseRefusalReason,
    ExpenseRefusedDTO,
    MemoryConflictAskedDTO,
    NonCommandGuidanceDTO,
    PendingCaptureDTO,
    ReminderListDTO,
    UnrecognisedCommandDTO,
)
from app.domains.events.public import (
    EventDTO,
    alert_not_set_to_type,
    event_dto_to_type,
)
from app.domains.events.public import EventLimitReached as EventLimitReachedDTO
from app.domains.expenses.public import (
    MAX_DESCRIPTION_LENGTH,
    ExpenseDTO,
    ExpenseSummary,
    ExpenseSummaryDTO,
    Paise,
    expense_dto_to_type,
    expense_summary_dto_to_type,
)
from app.domains.gateway.public import (
    MalformedResult,
    ProviderTimeout,
    ProviderUnavailable,
    SharedQuotaExhausted,
    UserLimitReached,
)
from app.domains.memories.public import (
    ConflictAnswer,
    MemoryDiscardedDTO,
    MemoryListDTO,
    MemorySavedDTO,
    MemoryTooLong,
    MemoryTooLongDTO,
    memory_dto_to_type,
    memory_too_long_to_type,
)
from app.domains.records.public import TaskDTO, task_dto_to_type
from app.domains.reminders.public import ReminderDTO, reminder_dto_to_type
from app.domains.reminders.public import (
    ReminderLimitReached as ReminderLimitReachedDTO,
)
from app.domains.search.public import (
    SearchResults,
    SearchResultsDTO,
    SearchTooLong,
    SearchTooLongDTO,
    search_results_to_type,
    search_too_long_to_type,
)
from app.graphql.permissions import IsAuthenticated

CaptureResult = Annotated[
    TaskCreated
    | TasksListed
    | ReminderCreated
    | RemindersListed
    | ReminderLimitReached
    | EventCreated
    | EventsListed
    | EventLimitReached
    | MemorySaved
    | MemoriesListed
    | MemoryTooLong
    | MemoryConflictAsked
    | SearchResults
    | SearchTooLong
    | ExpenseSaved
    | ExpenseQuestionAsked
    | ExpenseRefused
    | ExpenseSummary
    | PendingQuestionCreated
    | NonCommandGuidance
    | UnrecognisedCommand
    | UserLimitReached
    | ProviderUnavailable
    | ProviderTimeout
    | SharedQuotaExhausted
    | MalformedResult,
    strawberry.union("CaptureResult"),
]


def _capture_outcome_to_result(
    *, outcome: CaptureOutcome | AnswerOutcome
) -> CaptureResult:
    """The one place a capture outcome DTO becomes a GraphQL type."""
    memory_result = _memory_outcome_to_result(outcome=outcome)
    if memory_result is not None:
        return memory_result
    event_result = _event_outcome_to_result(outcome=outcome)
    if event_result is not None:
        return event_result
    expense_result = _expense_outcome_to_result(outcome=outcome)
    if expense_result is not None:
        return expense_result
    if isinstance(outcome, SearchResultsDTO):
        return cast(CaptureResult, search_results_to_type(results=outcome))
    if isinstance(outcome, SearchTooLongDTO):
        return cast(CaptureResult, search_too_long_to_type(too_long=outcome))
    if isinstance(outcome, ReminderDTO):
        return cast(
            CaptureResult,
            ReminderCreated(reminder=reminder_dto_to_type(reminder=outcome)),
        )
    if isinstance(outcome, ReminderListDTO):
        return cast(
            CaptureResult,
            RemindersListed(
                reminders=[
                    reminder_dto_to_type(reminder=reminder)
                    for reminder in outcome.reminders
                ]
            ),
        )
    if isinstance(outcome, ReminderLimitReachedDTO):
        return cast(
            CaptureResult,
            ReminderLimitReached(
                message=(
                    f"You have {outcome.limit} active reminders, the most Slashit "
                    "holds. Mark one done or delete one, then try again."
                ),
                limit=outcome.limit,
            ),
        )
    if isinstance(outcome, TaskDTO):
        return cast(CaptureResult, TaskCreated(task=task_dto_to_type(task=outcome)))
    if isinstance(outcome, list):
        return cast(
            CaptureResult,
            TasksListed(tasks=[task_dto_to_type(task=task) for task in outcome]),
        )
    if isinstance(outcome, PendingCaptureDTO):
        return cast(
            CaptureResult,
            PendingQuestionCreated(
                pending_capture_id=strawberry.ID(str(outcome.id)),
                question=outcome.question_text,
            ),
        )
    if isinstance(outcome, NonCommandGuidanceDTO):
        return cast(
            CaptureResult, NonCommandGuidance(original_input=outcome.original_input)
        )
    if isinstance(outcome, UnrecognisedCommandDTO):
        return cast(
            CaptureResult,
            UnrecognisedCommand(
                attempted_name=outcome.attempted_name,
                closest_matches=outcome.closest_matches,
            ),
        )
    # One of the gateway's five failure types, already a GraphQL type.
    return cast(CaptureResult, outcome)


def _event_outcome_to_result(
    *, outcome: CaptureOutcome | AnswerOutcome
) -> CaptureResult | None:
    """Epic 007's three outcomes, or None for any other."""
    if isinstance(outcome, EventDTO):
        return cast(
            CaptureResult,
            EventCreated(
                event=event_dto_to_type(event=outcome),
                alerts_not_set=[
                    alert_not_set_to_type(alert_not_set=alert_not_set)
                    for alert_not_set in outcome.alerts_not_set
                ],
            ),
        )
    if isinstance(outcome, EventListDTO):
        return cast(
            CaptureResult,
            EventsListed(
                events=[event_dto_to_type(event=event) for event in outcome.events]
            ),
        )
    if isinstance(outcome, EventLimitReachedDTO):
        return cast(
            CaptureResult,
            EventLimitReached(
                message=(
                    f"You have {outcome.limit} upcoming events, the most Slashit "
                    "holds. Delete one you no longer need, then try again. Past "
                    "events do not count."
                ),
                limit=outcome.limit,
            ),
        )
    return None


def _memory_outcome_to_result(
    *, outcome: CaptureOutcome | AnswerOutcome
) -> CaptureResult | None:
    """Epic 004's three outcomes, or None for any other."""
    if isinstance(outcome, MemorySavedDTO):
        return cast(
            CaptureResult,
            MemorySaved(
                memory=memory_dto_to_type(memory=outcome.memory),
                secret_caution=outcome.secret_caution,
            ),
        )
    if isinstance(outcome, MemoryListDTO):
        return cast(
            CaptureResult,
            MemoriesListed(
                memories=[
                    memory_dto_to_type(memory=memory) for memory in outcome.memories
                ],
                search_text=outcome.search_text,
            ),
        )
    if isinstance(outcome, MemoryTooLongDTO):
        return cast(CaptureResult, memory_too_long_to_type(too_long=outcome))
    if isinstance(outcome, MemoryConflictAskedDTO):
        return cast(
            CaptureResult,
            MemoryConflictAsked(
                pending_capture_id=strawberry.ID(str(outcome.pending_capture_id)),
                question=outcome.question,
                new_text=outcome.text,
                category=outcome.category,
                conflicting=[
                    memory_dto_to_type(memory=memory) for memory in outcome.conflicting
                ],
            ),
        )
    return None


def _expense_outcome_to_result(
    *, outcome: CaptureOutcome | AnswerOutcome
) -> CaptureResult | None:
    """Epic 006's four outcomes, or None for any other."""
    if isinstance(outcome, ExpenseDTO):
        return cast(
            CaptureResult, ExpenseSaved(expense=expense_dto_to_type(expense=outcome))
        )
    if isinstance(outcome, ExpenseQuestionAskedDTO):
        return cast(
            CaptureResult,
            ExpenseQuestionAsked(
                pending_capture_id=strawberry.ID(str(outcome.pending_capture_id)),
                kind=outcome.kind,
                question=outcome.question,
                amount_candidates=[
                    Paise(candidate) for candidate in outcome.amount_candidates
                ],
                read_date=outcome.read_date,
            ),
        )
    if isinstance(outcome, ExpenseSummaryDTO):
        return cast(CaptureResult, expense_summary_dto_to_type(summary=outcome))
    if isinstance(outcome, ExpenseRefusedDTO):
        return cast(
            CaptureResult,
            ExpenseRefused(
                message=_expense_refusal_message(refusal=outcome),
                reason=outcome.reason,
                length=outcome.length,
            ),
        )
    return None


def _expense_refusal_message(*, refusal: ExpenseRefusedDTO) -> str:
    """Design §8's copy for FR-6, FR-13 and FR-27."""
    if refusal.reason == ExpenseRefusalReason.FOREIGN_CURRENCY:
        return (
            "Slashit records rupees only for now. Enter the amount in ₹ and it "
            "will save."
        )
    if refusal.reason == ExpenseRefusalReason.AMOUNT_TOO_LARGE:
        return EXPENSE_AMOUNT_TOO_LARGE
    if refusal.reason == ExpenseRefusalReason.PERIOD_NOT_UNDERSTOOD:
        return (
            f"Slashit did not understand “{refusal.period_text}”. Try today, this "
            "week, last week, this month, last month, a month such as august, "
            "or this year."
        )
    return (
        f"That description is {refusal.length} characters. "
        f"It can be up to {MAX_DESCRIPTION_LENGTH}."
    )


ResolveMemoryConflictResult = Annotated[
    MemorySaved | MemoryDiscarded | PendingCaptureNotFound,
    strawberry.union("ResolveMemoryConflictResult"),
]


@strawberry.type
class CaptureMutations:
    @strawberry.mutation(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    async def submit_capture(self, info: Info, raw_input: str) -> CaptureResult:
        context = cast(Context, info.context)
        user_id = cast(UUID, context.user_id)
        interactor = build_submit_capture_interactor(context)
        outcome = await interactor.submit_capture(user_id=user_id, raw_input=raw_input)
        return _capture_outcome_to_result(outcome=outcome)

    @strawberry.mutation(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    async def answer_pending_capture(
        self, info: Info, pending_capture_id: strawberry.ID, answer: str
    ) -> CaptureResult:
        context = cast(Context, info.context)
        user_id = cast(UUID, context.user_id)
        interactor = build_answer_pending_capture_interactor(context)
        outcome = await interactor.answer_pending_capture(
            user_id=user_id,
            pending_capture_id=UUID(str(pending_capture_id)),
            answer=answer,
        )
        return _capture_outcome_to_result(outcome=outcome)

    @strawberry.mutation(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    async def discard_pending_capture(
        self, info: Info, pending_capture_id: strawberry.ID
    ) -> bool:
        context = cast(Context, info.context)
        user_id = cast(UUID, context.user_id)
        interactor = build_discard_pending_capture_interactor(context)
        await interactor.discard_pending_capture(
            user_id=user_id, pending_capture_id=UUID(str(pending_capture_id))
        )
        return True

    @strawberry.mutation(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    async def resolve_memory_conflict(
        self, info: Info, pending_capture_id: strawberry.ID, answer: ConflictAnswer
    ) -> ResolveMemoryConflictResult:
        """Epic 004, FR-11 to FR-13: the answer to "Which is correct?"."""
        context = cast(Context, info.context)
        user_id = cast(UUID, context.user_id)
        interactor = build_resolve_memory_conflict_interactor(context)
        outcome = await interactor.resolve_memory_conflict(
            user_id=user_id,
            pending_capture_id=UUID(str(pending_capture_id)),
            answer=answer,
        )
        if isinstance(outcome, MemorySavedDTO):
            return cast(
                ResolveMemoryConflictResult,
                MemorySaved(
                    memory=memory_dto_to_type(memory=outcome.memory),
                    secret_caution=outcome.secret_caution,
                ),
            )
        if isinstance(outcome, MemoryDiscardedDTO):
            return cast(
                ResolveMemoryConflictResult,
                MemoryDiscarded(
                    message="Kept your earlier memory. Nothing new was saved."
                ),
            )
        return cast(
            ResolveMemoryConflictResult,
            PendingCaptureNotFound(
                message="This question was already answered. Nothing changed."
            ),
        )
