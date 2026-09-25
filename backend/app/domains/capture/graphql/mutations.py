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
    build_submit_capture_interactor,
)
from app.domains.capture.graphql.types import (
    MemoriesListed,
    MemorySaved,
    NonCommandGuidance,
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
    NonCommandGuidanceDTO,
    PendingCaptureDTO,
    ReminderListDTO,
    UnrecognisedCommandDTO,
)
from app.domains.gateway.public import (
    MalformedResult,
    ProviderTimeout,
    ProviderUnavailable,
    SharedQuotaExhausted,
    UserLimitReached,
)
from app.domains.memories.public import (
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
from app.graphql.permissions import IsAuthenticated

CaptureResult = Annotated[
    TaskCreated
    | TasksListed
    | ReminderCreated
    | RemindersListed
    | ReminderLimitReached
    | MemorySaved
    | MemoriesListed
    | MemoryTooLong
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
    return None


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
