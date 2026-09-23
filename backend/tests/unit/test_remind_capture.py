"""`/remind` and `/reminders` through capture: TC-1.14, TC-1.15, TC-1.16."""

import uuid
from datetime import UTC, datetime
from typing import Any, cast
from zoneinfo import ZoneInfo

from strawberry.scalars import JSON

from app.domains.capture.adapters.gateway_extraction_adapter import (
    GatewayExtractionAdapter,
)
from app.domains.capture.interactors.answer_pending_capture import (
    AnswerPendingCaptureInteractor,
)
from app.domains.capture.interactors.submit_capture import SubmitCaptureInteractor
from app.domains.capture.interfaces.dtos import PendingCaptureDTO, ReminderListDTO
from app.domains.gateway.public import (
    Extraction,
    ExtractionRequest,
    ExtractionResult,
    ProviderUnavailable,
)
from app.domains.reminders.public import ReminderDTO
from tests.fakes.fake_analytics_port import FakeAnalyticsPort
from tests.fakes.fake_capture_turn_repository import FakeCaptureTurnRepository
from tests.fakes.fake_extraction_port import FakeExtractionPort
from tests.fakes.fake_pending_capture_repository import FakePendingCaptureRepository
from tests.fakes.fake_reminder_port import FakeReminderPort, fake_reminder_capture
from tests.fakes.fake_task_port import FakeTaskPort

KOLKATA = ZoneInfo("Asia/Kolkata")
NOW = datetime(2026, 9, 23, 10, 0, tzinfo=KOLKATA).astimezone(UTC)


def _reminder_extraction(**fields: Any) -> Extraction:
    return Extraction(
        data=cast(JSON, fields), model="fake", input_tokens=1, output_tokens=1
    )


def _submit(
    *, extraction: FakeExtractionPort
) -> tuple[
    SubmitCaptureInteractor,
    FakeReminderPort,
    FakePendingCaptureRepository,
    FakeCaptureTurnRepository,
]:
    reminder_port = FakeReminderPort(now_provider=lambda: NOW)
    pending = FakePendingCaptureRepository()
    turns = FakeCaptureTurnRepository()
    interactor = SubmitCaptureInteractor(
        pending_capture_repository=pending,
        capture_turn_repository=turns,
        task_port=FakeTaskPort(),
        extraction=extraction,
        analytics=FakeAnalyticsPort(),
        reminder_port=reminder_port,
        reminder_capture=fake_reminder_capture(
            extraction=extraction, reminder_port=reminder_port
        ),
    )
    return interactor, reminder_port, pending, turns


async def test_remind_with_a_date_and_time_creates_and_logs_the_turn() -> None:
    extraction = FakeExtractionPort(
        result=_reminder_extraction(
            description="Call Mom", local_date="2026-09-24", local_time="19:00"
        )
    )
    interactor, _, _, turns = _submit(extraction=extraction)

    outcome = await interactor.submit_capture(
        user_id=uuid.uuid4(), raw_input="/remind Call Mom tomorrow at 7pm"
    )

    assert isinstance(outcome, ReminderDTO)
    assert outcome.summary.when_text == "Tomorrow, 7:00 PM"
    assert extraction.calls == ["Call Mom tomorrow at 7pm"]
    assert turns.rows[0].outcome == "reminder_created"
    assert turns.rows[0].resulting_reminder_id == outcome.id


async def test_remind_with_no_date_asks_one_question_and_writes_nothing() -> None:
    """TC-1.14, FR-2."""
    extraction = FakeExtractionPort(
        result=_reminder_extraction(description="Call the plumber")
    )
    interactor, reminder_port, _, _ = _submit(extraction=extraction)
    user_id = uuid.uuid4()

    outcome = await interactor.submit_capture(
        user_id=user_id, raw_input="/remind call the plumber"
    )

    assert isinstance(outcome, PendingCaptureDTO)
    assert outcome.question_text == "When should I remind you to call the plumber?"
    assert outcome.missing_field == "remind_at"
    assert reminder_port.repository.rows == {}


async def test_answering_when_creates_the_reminder() -> None:
    """TC-1.15, FR-2: the answer is read with the known description."""
    extraction = FakeExtractionPort(
        results=[
            _reminder_extraction(description="Call the plumber"),
            _reminder_extraction(
                description="Call the plumber",
                local_date="2026-09-24",
                local_time="09:00",
            ),
        ]
    )
    submit, reminder_port, pending_repo, turns = _submit(extraction=extraction)
    user_id = uuid.uuid4()
    question = await submit.submit_capture(
        user_id=user_id, raw_input="/remind call the plumber"
    )
    assert isinstance(question, PendingCaptureDTO)
    answer = AnswerPendingCaptureInteractor(
        pending_capture_repository=pending_repo,
        capture_turn_repository=turns,
        task_port=FakeTaskPort(),
        extraction=extraction,
        reminder_capture=fake_reminder_capture(
            extraction=extraction, reminder_port=reminder_port
        ),
    )

    outcome = await answer.answer_pending_capture(
        user_id=user_id, pending_capture_id=question.id, answer="tomorrow at 9"
    )

    assert isinstance(outcome, ReminderDTO)
    assert extraction.calls[-1] == "Call the plumber tomorrow at 9"
    assert (
        await pending_repo.get_pending_capture(
            user_id=user_id, pending_capture_id=question.id
        )
        is None
    )


async def test_remind_with_nothing_asks_what_to_remind_about() -> None:
    interactor, _, _, _ = _submit(extraction=FakeExtractionPort(results=[]))

    outcome = await interactor.submit_capture(user_id=uuid.uuid4(), raw_input="/remind")

    assert isinstance(outcome, PendingCaptureDTO)
    assert outcome.question_text == "What should I remind you about?"


async def test_remind_when_the_model_is_down_returns_the_gateway_refusal() -> None:
    """RemindModelDown: nothing saved, the turn logged as refused."""
    refusal = ProviderUnavailable(message="The model provider is unavailable")
    interactor, reminder_port, _, turns = _submit(
        extraction=FakeExtractionPort(result=refusal)
    )

    outcome = await interactor.submit_capture(
        user_id=uuid.uuid4(), raw_input="/remind call Mom at 7pm"
    )

    assert outcome == refusal
    assert reminder_port.repository.rows == {}
    assert turns.rows[0].outcome == "refused"


async def test_reminders_lists_the_active_ones() -> None:
    """FR-25."""
    extraction = FakeExtractionPort(
        result=_reminder_extraction(
            description="Call Mom", local_date="2026-09-24", local_time="19:00"
        )
    )
    interactor, _, _, _ = _submit(extraction=extraction)
    user_id = uuid.uuid4()
    created = await interactor.submit_capture(
        user_id=user_id, raw_input="/remind Call Mom tomorrow at 7pm"
    )

    listed = await interactor.submit_capture(user_id=user_id, raw_input="/reminders")

    assert isinstance(created, ReminderDTO)
    assert isinstance(listed, ReminderListDTO)
    assert [item.id for item in listed.reminders] == [created.id]


class _RecordingExtractInteractor:
    def __init__(self) -> None:
        self.instructions: list[str] = []

    async def extract(
        self, *, user_id: uuid.UUID, request: ExtractionRequest
    ) -> ExtractionResult:
        self.instructions.append(str(request.instruction))
        return _reminder_extraction(description="x")


class _KolkataClock:
    async def local_now(self, *, user_id: uuid.UUID) -> tuple[datetime, str]:
        return NOW.astimezone(KOLKATA), "Asia/Kolkata"


async def test_every_extraction_reads_dates_against_the_users_local_now() -> None:
    """TC-1.16, AD-7: task capture included, since it shares this adapter."""
    extract = _RecordingExtractInteractor()
    adapter = GatewayExtractionAdapter(
        extract_interactor=cast(Any, extract), local_clock=_KolkataClock()
    )

    await adapter.extract(
        user_id=uuid.uuid4(),
        prompt="Finish docs tomorrow",
        schema={},
        instruction="Extract the task.",
    )

    assert extract.instructions == [
        "Extract the task. Now is 2026-09-23T10:00:00+05:30 (Asia/Kolkata)."
    ]
