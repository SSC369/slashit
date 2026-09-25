"""Answering a pending capture. See 04.1-capture-core.md section 7. FR-37, FR-38."""

import uuid

import pytest

from app.domains.capture.interactors.answer_pending_capture import (
    AnswerCouldNotBeUnderstoodError,
    AnswerPendingCaptureInteractor,
    PendingCaptureNotFoundError,
)
from app.domains.records.public import TaskDTO
from tests.fakes.fake_capture_turn_repository import FakeCaptureTurnRepository
from tests.fakes.fake_extraction_port import FakeExtractionPort, extraction
from tests.fakes.fake_pending_capture_repository import FakePendingCaptureRepository
from tests.fakes.fake_reminder_port import fake_reminder_capture
from tests.fakes.fake_task_port import FakeTaskPort


async def test_answering_a_title_question_creates_the_task() -> None:
    """T-1.7: FR-37. T-4.5: writes one task_created turn, correlated to the
    pending capture it resolved."""
    task_port = FakeTaskPort()
    pending_repo = FakePendingCaptureRepository()
    user_id = uuid.uuid4()
    pending = await pending_repo.create_pending_capture(
        user_id=user_id,
        command_name="/add-task",
        known_title=None,
        missing_field="title",
        question_text="What should the task be called?",
        original_input="/add-task",
    )
    turn_repo = FakeCaptureTurnRepository()
    interactor = AnswerPendingCaptureInteractor(
        pending_capture_repository=pending_repo,
        capture_turn_repository=turn_repo,
        task_port=task_port,
        extraction=FakeExtractionPort(result=extraction()),
        reminder_capture=fake_reminder_capture(
            extraction=FakeExtractionPort(result=extraction())
        ),
    )

    task = await interactor.answer_pending_capture(
        user_id=user_id, pending_capture_id=pending.id, answer="Buy milk"
    )
    assert isinstance(task, TaskDTO)

    assert task.title == "Buy milk"
    assert pending.id not in pending_repo.rows

    assert len(turn_repo.rows) == 1
    turn = turn_repo.rows[0]
    assert turn.outcome == "task_created"
    assert turn.resulting_task_id == task.id
    assert turn.resulting_pending_capture_id == pending.id
    assert turn.question_text == "What should the task be called?"
    assert turn.answer_text == "Buy milk"
    assert turn.input_text == "/add-task"


async def test_answering_a_due_date_question_resolves_it_and_creates_the_task() -> None:
    """T-1.7: FR-37, FR-38. The answer resolves against the original capture's
    own original_input, not a fresh one."""
    task_port = FakeTaskPort()
    pending_repo = FakePendingCaptureRepository()
    user_id = uuid.uuid4()
    pending = await pending_repo.create_pending_capture(
        user_id=user_id,
        command_name="/add-task",
        known_title="Buy milk",
        missing_field="due_at",
        question_text='When is "Buy milk" due?',
        original_input="/add-task buy milk",
    )
    extraction_port = FakeExtractionPort(
        result=extraction(due_at="2026-09-18T00:00:00+00:00")
    )
    turn_repo = FakeCaptureTurnRepository()
    interactor = AnswerPendingCaptureInteractor(
        pending_capture_repository=pending_repo,
        capture_turn_repository=turn_repo,
        task_port=task_port,
        extraction=extraction_port,
        reminder_capture=fake_reminder_capture(
            extraction=FakeExtractionPort(result=extraction())
        ),
    )

    task = await interactor.answer_pending_capture(
        user_id=user_id, pending_capture_id=pending.id, answer="Friday"
    )
    assert isinstance(task, TaskDTO)

    assert task.title == "Buy milk"
    assert task.due_at is not None
    assert task.original_input == "/add-task buy milk"
    assert turn_repo.rows[0].answer_text == "Friday"


async def test_unresolvable_due_date_answer_raises() -> None:
    """T-4.5: the raised-exception path writes no turn."""
    pending_repo = FakePendingCaptureRepository()
    user_id = uuid.uuid4()
    pending = await pending_repo.create_pending_capture(
        user_id=user_id,
        command_name="/add-task",
        known_title="Buy milk",
        missing_field="due_at",
        question_text='When is "Buy milk" due?',
        original_input="/add-task buy milk",
    )
    turn_repo = FakeCaptureTurnRepository()
    interactor = AnswerPendingCaptureInteractor(
        pending_capture_repository=pending_repo,
        capture_turn_repository=turn_repo,
        task_port=FakeTaskPort(),
        extraction=FakeExtractionPort(result=extraction()),  # no due_at
        reminder_capture=fake_reminder_capture(
            extraction=FakeExtractionPort(result=extraction())
        ),
    )

    with pytest.raises(AnswerCouldNotBeUnderstoodError):
        await interactor.answer_pending_capture(
            user_id=user_id, pending_capture_id=pending.id, answer="whenever"
        )

    assert turn_repo.rows == []


async def test_answering_a_pending_capture_that_does_not_exist_raises() -> None:
    """T-1.11: not found is a plain error, not a screen."""
    interactor = AnswerPendingCaptureInteractor(
        pending_capture_repository=FakePendingCaptureRepository(),
        capture_turn_repository=FakeCaptureTurnRepository(),
        task_port=FakeTaskPort(),
        extraction=FakeExtractionPort(result=extraction()),
        reminder_capture=fake_reminder_capture(
            extraction=FakeExtractionPort(result=extraction())
        ),
    )

    with pytest.raises(PendingCaptureNotFoundError):
        await interactor.answer_pending_capture(
            user_id=uuid.uuid4(), pending_capture_id=uuid.uuid4(), answer="Buy milk"
        )


async def test_answering_another_users_pending_capture_raises_not_found() -> None:
    """T-1.11 (boundary half): rule T7."""
    pending_repo = FakePendingCaptureRepository()
    owner_id = uuid.uuid4()
    pending = await pending_repo.create_pending_capture(
        user_id=owner_id,
        command_name="/add-task",
        known_title=None,
        missing_field="title",
        question_text="What should the task be called?",
        original_input="/add-task",
    )
    interactor = AnswerPendingCaptureInteractor(
        pending_capture_repository=pending_repo,
        capture_turn_repository=FakeCaptureTurnRepository(),
        task_port=FakeTaskPort(),
        extraction=FakeExtractionPort(result=extraction()),
        reminder_capture=fake_reminder_capture(
            extraction=FakeExtractionPort(result=extraction())
        ),
    )

    with pytest.raises(PendingCaptureNotFoundError):
        await interactor.answer_pending_capture(
            user_id=uuid.uuid4(), pending_capture_id=pending.id, answer="Buy milk"
        )
