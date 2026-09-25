"""Capture's one use case. See 04.1-capture-core.md section 7 (test ids
renumbered 2026-09-13 after /complete-task and /delete-task were removed)."""

import uuid
from datetime import UTC, datetime

import pytest

from app.domains.capture.constants import MAX_INPUT_LENGTH
from app.domains.capture.interactors.submit_capture import SubmitCaptureInteractor
from app.domains.capture.interfaces.dtos import (
    NonCommandGuidanceDTO,
    PendingCaptureDTO,
    UnrecognisedCommandDTO,
)
from app.domains.gateway.errors import (
    MalformedResult,
    MalformedResultError,
    ProviderTimeout,
    ProviderTimeoutError,
    ProviderUnavailable,
    ProviderUnavailableError,
    SharedQuotaExhausted,
    SharedQuotaExhaustedError,
    UserLimitReached,
    UserLimitReachedError,
)
from app.domains.records.public import TaskDTO
from tests.fakes.fake_analytics_port import FakeAnalyticsPort
from tests.fakes.fake_capture_turn_repository import FakeCaptureTurnRepository
from tests.fakes.fake_extraction_port import FakeExtractionPort, extraction
from tests.fakes.fake_memory_port import FakeMemoryPort
from tests.fakes.fake_pending_capture_repository import FakePendingCaptureRepository
from tests.fakes.fake_reminder_port import FakeReminderPort, fake_reminder_capture
from tests.fakes.fake_task_port import FakeTaskPort


def _interactor(
    *, extraction_port: FakeExtractionPort | None = None
) -> tuple[
    SubmitCaptureInteractor,
    FakeTaskPort,
    FakePendingCaptureRepository,
    FakeCaptureTurnRepository,
    FakeAnalyticsPort,
]:
    task_port = FakeTaskPort()
    pending_capture_repository = FakePendingCaptureRepository()
    capture_turn_repository = FakeCaptureTurnRepository()
    analytics = FakeAnalyticsPort()
    resolved_extraction = extraction_port or FakeExtractionPort(result=extraction())
    interactor = SubmitCaptureInteractor(
        memory_port=FakeMemoryPort(),
        pending_capture_repository=pending_capture_repository,
        capture_turn_repository=capture_turn_repository,
        task_port=task_port,
        extraction=resolved_extraction,
        analytics=analytics,
        reminder_port=FakeReminderPort(),
        reminder_capture=fake_reminder_capture(extraction=resolved_extraction),
    )
    return (
        interactor,
        task_port,
        pending_capture_repository,
        capture_turn_repository,
        analytics,
    )


async def test_empty_input_after_trimming_raises() -> None:
    """T-1.1."""
    interactor, _, _, _, _ = _interactor()

    with pytest.raises(ValueError):
        await interactor.submit_capture(user_id=uuid.uuid4(), raw_input="   ")


async def test_input_over_length_raises() -> None:
    """T-1.2: AD-4."""
    interactor, _, _, _, _ = _interactor()

    with pytest.raises(ValueError):
        await interactor.submit_capture(
            user_id=uuid.uuid4(), raw_input="a" * (MAX_INPUT_LENGTH + 1)
        )


async def test_non_command_input_returns_guidance_with_original_text() -> None:
    """T-1.3: FR-9."""
    interactor, *_ = _interactor()

    result = await interactor.submit_capture(
        user_id=uuid.uuid4(), raw_input="buy milk tomorrow"
    )

    assert isinstance(result, NonCommandGuidanceDTO)
    assert result.original_input == "buy milk tomorrow"


async def test_non_command_input_logs_the_fr9_metric_event() -> None:
    """PRD section 8: sessions where the user typed without a command."""
    interactor, _, _, _, analytics = _interactor()
    user_id = uuid.uuid4()

    await interactor.submit_capture(user_id=user_id, raw_input="buy milk tomorrow")

    assert analytics.no_command_input_calls == [user_id]


async def test_unknown_command_returns_unrecognised() -> None:
    """T-1.4: FR-12."""
    interactor, *_ = _interactor()

    result = await interactor.submit_capture(
        user_id=uuid.uuid4(), raw_input="/add-tsk buy milk"
    )

    assert isinstance(result, UnrecognisedCommandDTO)
    assert result.attempted_name == "/add-tsk"
    assert "/add-task" in result.closest_matches


async def test_add_task_with_title_and_due_creates_a_task() -> None:
    """T-1.5: FR-6, FR-7."""
    extraction_port = FakeExtractionPort(
        result=extraction(title="Finish docs", due_at="2026-09-14T00:00:00+00:00")
    )
    interactor, task_port, _, turn_repo, _ = _interactor(
        extraction_port=extraction_port
    )

    result = await interactor.submit_capture(
        user_id=uuid.uuid4(), raw_input="/add-task finish docs tomorrow"
    )

    assert isinstance(result, TaskDTO)
    assert result.title == "Finish docs"
    assert result.due_at is not None
    assert len(task_port.created_tasks) == 1

    assert len(turn_repo.rows) == 1
    assert turn_repo.rows[0].outcome == "task_created"
    assert turn_repo.rows[0].resulting_task_id == result.id
    assert turn_repo.rows[0].resulting_pending_capture_id is None


async def test_add_task_with_no_arguments_asks_for_a_title() -> None:
    """T-1.6 (title branch): FR-8. T-4.2."""
    interactor, task_port, pending_repo, turn_repo, _ = _interactor()

    result = await interactor.submit_capture(
        user_id=uuid.uuid4(), raw_input="/add-task"
    )

    assert isinstance(result, PendingCaptureDTO)
    assert result.missing_field == "title"
    assert task_port.created_tasks == []
    assert len(pending_repo.rows) == 1

    assert len(turn_repo.rows) == 1
    assert turn_repo.rows[0].outcome == "question_asked"
    assert turn_repo.rows[0].resulting_pending_capture_id == result.id
    assert turn_repo.rows[0].question_text == result.question_text
    assert turn_repo.rows[0].resulting_task_id is None


async def test_add_task_missing_due_date_asks_for_it() -> None:
    """T-1.6: FR-8."""
    extraction_port = FakeExtractionPort(result=extraction(title="Buy milk"))
    interactor, task_port, pending_repo, turn_repo, _ = _interactor(
        extraction_port=extraction_port
    )

    result = await interactor.submit_capture(
        user_id=uuid.uuid4(), raw_input="/add-task buy milk"
    )

    assert isinstance(result, PendingCaptureDTO)
    assert result.missing_field == "due_at"
    assert result.known_title == "Buy milk"
    assert task_port.created_tasks == []
    assert len(pending_repo.rows) == 1
    assert len(turn_repo.rows) == 1


async def test_tasks_lists_open_tasks_and_writes_no_turn() -> None:
    """T-1.9 (renumbered): FR-25. T-4.4: `/tasks` is a read, not a capture."""
    interactor, task_port, _, turn_repo, _ = _interactor()
    user_id = uuid.uuid4()
    await task_port.create_task(
        user_id=user_id, title="Existing", due_at=None, original_input="/add-task x"
    )

    result = await interactor.submit_capture(user_id=user_id, raw_input="/tasks")

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].title == "Existing"
    assert turn_repo.rows == []


async def test_non_command_and_unrecognised_command_write_no_turn() -> None:
    """T-4.4: guidance outcomes are not capture attempts."""
    interactor, _, _, turn_repo, _ = _interactor()

    await interactor.submit_capture(user_id=uuid.uuid4(), raw_input="buy milk")
    await interactor.submit_capture(user_id=uuid.uuid4(), raw_input="/add-tsk x")

    assert turn_repo.rows == []


@pytest.mark.parametrize(
    ("raised", "expected_type"),
    [
        (
            UserLimitReachedError(limit=20, resets_at=datetime.now(UTC)),
            UserLimitReached,
        ),
        (ProviderUnavailableError(), ProviderUnavailable),
        (ProviderTimeoutError(8.0), ProviderTimeout),
        (SharedQuotaExhaustedError(), SharedQuotaExhausted),
        (MalformedResultError("bad shape"), MalformedResult),
    ],
)
async def test_each_gateway_failure_passes_through_unmapped(
    raised: Exception, expected_type: type
) -> None:
    """T-1.10 (renumbered): FR-35. Capture does not redefine these types.
    T-4.3: each also writes one refused turn."""
    gql_error = raised.to_gql()  # type: ignore[attr-defined]
    extraction_port = FakeExtractionPort(result=gql_error)
    interactor, task_port, _, turn_repo, _ = _interactor(
        extraction_port=extraction_port
    )

    result = await interactor.submit_capture(
        user_id=uuid.uuid4(), raw_input="/add-task finish docs tomorrow"
    )

    assert isinstance(result, expected_type)
    assert task_port.created_tasks == []

    assert len(turn_repo.rows) == 1
    assert turn_repo.rows[0].outcome == "refused"
    assert turn_repo.rows[0].resulting_task_id is None
    assert turn_repo.rows[0].resulting_pending_capture_id is None
